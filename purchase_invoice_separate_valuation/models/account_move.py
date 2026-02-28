# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)

# All move types that represent vendor billing documents.
_VENDOR_BILL_TYPES = frozenset({'in_invoice', 'in_refund', 'in_receipt'})

# Move types that can be designated as the Final Invoice.
# Credit notes are excluded: a reversal document should not close the billing cycle.
_FINAL_INVOICE_TYPES = frozenset({'in_invoice', 'in_receipt'})


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_final_invoice = fields.Boolean(
        string='Final Invoice',
        default=False,
        copy=False,
    )
    price_adjustment_move_id = fields.Many2one(
        'account.move',
        string='Price Adjustment Entry',
        readonly=True,
        ondelete='set null',
    )
    po_has_other_final_invoice = fields.Boolean(
        string='PO Has Other Final Invoice',
        compute='_compute_po_has_other_final_invoice',
    )
    po_use_separate_valuation = fields.Boolean(
        string='PO Uses Separate Valuation',
        compute='_compute_po_use_separate_valuation',
        help='True when the linked purchase order uses separate valuation mode.',
    )

    @api.depends(
        'purchase_id',
        'purchase_id.use_separate_valuation',
        'invoice_line_ids.purchase_line_id.order_id',
        'invoice_line_ids.purchase_line_id.order_id.use_separate_valuation',
    )
    def _compute_po_use_separate_valuation(self):
        for move in self:
            purchase = move._get_linked_purchase_order()
            move.po_use_separate_valuation = bool(
                purchase and purchase.use_separate_valuation
            )

    @api.depends(
        'purchase_id',
        'invoice_line_ids.purchase_line_id.order_id',
        'purchase_id.order_line.invoice_lines.move_id.is_final_invoice',
        'purchase_id.order_line.invoice_lines.move_id.state',
    )
    def _compute_po_has_other_final_invoice(self):
        for move in self:
            purchase = move._get_linked_purchase_order()
            if not purchase:
                move.po_has_other_final_invoice = False
                continue
            move.po_has_other_final_invoice = bool(move._get_po_final_invoices(purchase))

    def _post(self, soft=True):
        """Post moves and trigger GRNI balancing for final vendor bills.

        SVL / price-difference creation for vendor bills is blocked at the line
        level via AccountMoveLine._apply_price_difference(), so the full super()
        MRO chain can run safely. This override only adds the GRNI
        synchronisation step afterwards.
        """
        # Run pre-post validation only on records that will actually be posted.
        # With soft=True, Odoo skips moves not in 'draft' state; running checks
        # on those would raise false-positive errors.
        to_post = self.filtered(lambda m: m.state == 'draft') if soft else self

        for bill in to_post.filtered(
            lambda m: m.is_final_invoice and m.move_type in _VENDOR_BILL_TYPES
        ):
            bill._check_no_existing_final_invoice()
            bill._check_price_adjustment_account_configured()

        for bill in to_post.filtered(
            lambda m: not m.is_final_invoice and m.move_type in _VENDOR_BILL_TYPES
        ):
            bill._check_no_bill_after_final_invoice()

        result = super()._post(soft)

        # Sync final vendor bills that were just posted.
        already_synced = self.env['account.move']
        for bill in result.filtered(
            lambda m: m.is_final_invoice and m.move_type in _VENDOR_BILL_TYPES
        ):
            bill._sync_price_adjustment_entry()
            already_synced |= bill

        # When a non-final vendor bill (e.g. credit note / reversal) is posted,
        # re-sync the GRNI adjustment of any existing final invoice on the same PO.
        # Exclude invoices already synced above to avoid a redundant double-sync.
        final_invoices_to_sync = self.env['account.move']
        for bill in result.filtered(
            lambda m: not m.is_final_invoice and m.move_type in _VENDOR_BILL_TYPES
        ):
            purchase = bill._get_linked_purchase_order()
            if purchase:
                final_invoices_to_sync |= bill._get_po_final_invoices(purchase)

        for final_inv in final_invoices_to_sync - already_synced:
            final_inv._sync_price_adjustment_entry()

        return result

    # ------------------------------------------------------------------
    # GRNI adjustment helpers
    # ------------------------------------------------------------------

    def _sync_price_adjustment_entry(self):
        """Create / update the GRNI balancing entry for a final vendor bill.
        Protected against re-entrant calls (e.g. _post() + write() both firing
        for the same invoice) via the skip_price_adjustment_sync context key.
        """
        self.ensure_one()
        if self.env.context.get('skip_price_adjustment_sync'):
            return
        _logger.debug('_sync_price_adjustment_entry: %s (is_final=%s)', self.name, self.is_final_invoice)

        if (
            not self.is_final_invoice
            or self.state != 'posted'
            or self.move_type not in _VENDOR_BILL_TYPES
        ):
            if self.price_adjustment_move_id:
                _logger.debug('Removing adjustment entry – invoice is no longer final or posted')
                self._remove_price_adjustment_entry()
            return

        purchase = self._get_linked_purchase_order()
        if not purchase:
            _logger.warning('_sync_price_adjustment_entry: no linked PO found for %s', self.name)
            return

        # --- Collect GRNI account IDs from PO products ---
        stock_input_account_ids = self._get_purchase_stock_input_account_ids(purchase)

        if not stock_input_account_ids:
            _logger.debug('_sync_price_adjustment_entry: no GRNI accounts found')
            return

        self._check_price_adjustment_account_configured(
            purchase=purchase,
            stock_input_account_ids=stock_input_account_ids,
        )
        price_adjustment_account = self.company_id.purchase_price_adjustment_account_id

        # Resolve the journal for the GRNI adjustment entry.
        # Use the dedicated GRNI journal when configured; fall back to the first
        # general-type journal of the company so that the entry never lands in
        # the AP journal by accident.
        grni_journal = self.company_id.purchase_grni_adjustment_journal_id
        if not grni_journal:
            grni_journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        if not grni_journal:
            _logger.warning(
                '_sync_price_adjustment_entry: no suitable journal found for GRNI adjustment'
            )
            return

        # --- Receipt side: GRNI debits/credits from done stock moves ---
        done_moves = purchase.order_line.mapped('move_ids').filtered(
            lambda m: m.state == 'done'
            and m.product_id
            and m.product_id.type == 'product'
            and m.product_id.categ_id.property_valuation == 'real_time'
        )
        receipt_balances = {}
        if done_moves:
            for aml in done_moves.mapped('account_move_ids.line_ids').filtered(
                lambda l: l.account_id.id in stock_input_account_ids and l.move_id.state == 'posted'
            ):
                receipt_balances.setdefault(aml.account_id.id, 0.0)
                receipt_balances[aml.account_id.id] += aml.balance

        # --- Invoice side: GRNI lines from all PO-linked vendor bills ---
        po_bills = purchase.order_line.mapped('invoice_lines.move_id').filtered(
            lambda m: m.state == 'posted' and m.move_type in _VENDOR_BILL_TYPES
        )
        invoice_balances = {}
        if po_bills:
            for aml in self.env['account.move.line'].search([
                ('move_id', 'in', po_bills.ids),
                ('account_id', 'in', list(stock_input_account_ids)),
            ]):
                invoice_balances.setdefault(aml.account_id.id, 0.0)
                invoice_balances[aml.account_id.id] += aml.balance

        # --- Build adjustment lines ---
        precision_rounding = self.company_id.currency_id.rounding
        adjustment_lines = []

        for account_id in set(receipt_balances) | set(invoice_balances):
            total_balance = (
                receipt_balances.get(account_id, 0.0)
                + invoice_balances.get(account_id, 0.0)
            )
            if float_is_zero(total_balance, precision_rounding=precision_rounding):
                continue

            stock_input_account = self.env['account.account'].browse(account_id)
            amount = abs(total_balance)
            _logger.debug(
                'GRNI balance for %s: %s', stock_input_account.display_name, total_balance
            )

            if total_balance > 0:
                # Debit balance → credit GRNI, debit price-adjustment account
                adjustment_lines += [
                    self._grni_line_vals(price_adjustment_account.id, debit=amount),
                    self._grni_line_vals(account_id, credit=amount),
                ]
            else:
                # Credit balance → debit GRNI, credit price-adjustment account
                adjustment_lines += [
                    self._grni_line_vals(account_id, debit=amount),
                    self._grni_line_vals(price_adjustment_account.id, credit=amount),
                ]

        if adjustment_lines:
            if self.price_adjustment_move_id:
                self._remove_price_adjustment_entry()

            adj_move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': grni_journal.id,
                'date': self.date,
                'ref': _('GRNI Adjustment – Final Invoice %s') % self.name,
                'line_ids': [(0, 0, v) for v in adjustment_lines],
            })
            adj_move.action_post()
            self.with_context(skip_price_adjustment_sync=True).write({
                'price_adjustment_move_id': adj_move.id,
            })
            _logger.debug('GRNI adjustment entry created: %s', adj_move.name)
        else:
            _logger.debug('GRNI already balanced – no adjustment needed')
            if self.price_adjustment_move_id:
                self._remove_price_adjustment_entry()

    def _grni_line_vals(self, account_id, debit=0.0, credit=0.0):
        return {
            'name': _('GRNI adjustment (Final Invoice %s)') % self.name,
            'account_id': account_id,
            'debit': debit,
            'credit': credit,
            'partner_id': self.partner_id.id,
        }

    def _remove_price_adjustment_entry(self):
        """Cancel and delete the linked GRNI adjustment entry.

        Raises UserError if the entry cannot be reset to draft (e.g. because it
        has already been reconciled), so the caller is clearly informed instead
        of leaving the system in a silent inconsistent state.
        """
        self.ensure_one()
        adj = self.price_adjustment_move_id
        if not adj:
            return
        try:
            if adj.state == 'posted':
                adj.button_draft()
            adj.unlink()
        except Exception as e:
            _logger.exception('Failed to remove GRNI adjustment entry %s', adj.name)
            raise UserError(_(
                'Could not remove the GRNI adjustment entry %s.\n'
                'Please unreconcile or manually reverse it first.\n\nDetail: %s'
            ) % (adj.name, str(e))) from e
        self.with_context(skip_price_adjustment_sync=True).write({
            'price_adjustment_move_id': False,
        })

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_price_adjustment_sync'):
            return res
        # Sync when is_final_invoice changes (covers both toggling on and off).
        # Sync on purchase_id change only for final invoices – non-final invoices
        # have no adjustment entry and don't need a round-trip to _sync.
        if 'is_final_invoice' in vals:
            trigger_moves = self.filtered(
                lambda m: m.state == 'posted' and m.move_type in _VENDOR_BILL_TYPES
            )
        elif 'purchase_id' in vals:
            trigger_moves = self.filtered(
                lambda m: m.is_final_invoice
                and m.state == 'posted'
                and m.move_type in _VENDOR_BILL_TYPES
            )
        else:
            trigger_moves = self.env['account.move']
        for move in trigger_moves:
            move._sync_price_adjustment_entry()
        return res

    def button_draft(self):
        """On reset-to-draft, keep GRNI adjustment entries consistent.

        - Final invoice reset to draft: _sync detects state != 'posted' and
          removes the adjustment entry.
        - Non-final bill reset to draft: re-sync the linked PO's final invoice
          so its adjustment reflects the updated invoice balance.
        """
        result = super().button_draft()
        if self.env.context.get('skip_price_adjustment_sync'):
            return result
        final_invoices_to_sync = self.env['account.move']
        for move in self.filtered(lambda m: m.move_type in _VENDOR_BILL_TYPES):
            if move.is_final_invoice:
                # _sync will detect state != 'posted' and remove the adjustment.
                final_invoices_to_sync |= move
            else:
                purchase = move._get_linked_purchase_order()
                if purchase:
                    final_invoices_to_sync |= move._get_po_final_invoices(purchase)
        for final_inv in final_invoices_to_sync:
            final_inv._sync_price_adjustment_entry()
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_linked_purchase_order(self):
        """Return the purchase order linked to this vendor bill."""
        self.ensure_one()
        purchase = self.purchase_id
        if not purchase:
            purchase = self.invoice_line_ids.mapped('purchase_line_id.order_id')[:1]
        return purchase

    def _get_po_final_invoices(self, purchase):
        """Return posted final invoices for purchase, excluding self.

        Used for both validation (does another final invoice exist?) and
        re-sync triggering (which final invoices need their adjustment updated?).
        """
        self.ensure_one()
        return purchase.order_line.mapped('invoice_lines.move_id').filtered(
            lambda m: m.id != self.id
            and m.is_final_invoice
            and m.state == 'posted'
            and m.move_type in _VENDOR_BILL_TYPES
        )

    def _get_purchase_stock_input_account_ids(self, purchase):
        """Return stock-input account IDs found on the purchase order lines."""
        account_ids = set()
        for line in purchase.order_line.filtered('product_id'):
            account = line.product_id.product_tmpl_id._get_product_accounts().get('stock_input')
            if account:
                account_ids.add(account.id)
        return account_ids

    def _check_price_adjustment_account_configured(self, purchase=None, stock_input_account_ids=None):
        """Raise if a final invoice needs GRNI adjustment but account is not configured."""
        self.ensure_one()
        purchase = purchase or self._get_linked_purchase_order()
        if not purchase:
            return
        account_ids = stock_input_account_ids
        if account_ids is None:
            account_ids = self._get_purchase_stock_input_account_ids(purchase)
        if account_ids and not self.company_id.purchase_price_adjustment_account_id:
            raise UserError(_(
                'Please configure "Purchase Price Adjustment Account" in Accounting settings '
                'before posting Final Invoice %s.'
            ) % (self.display_name or self.name))

    def _check_no_existing_final_invoice(self):
        """Raise if the linked PO already has a posted final invoice."""
        self.ensure_one()
        purchase = self._get_linked_purchase_order()
        if not purchase:
            return
        existing = self._get_po_final_invoices(purchase)
        if existing:
            raise UserError(_(
                'Purchase order %s already has a final invoice: %s.\n'
                'Please remove the existing final invoice status first.'
            ) % (purchase.name, existing[0].name))

    def _check_no_bill_after_final_invoice(self):
        """Raise if trying to post a vendor bill when the linked PO already has
        a posted final invoice.

        Applies only to separate-valuation POs.  Credit notes (in_refund) are
        intentionally excluded so that corrections / reversals remain possible
        after the final invoice has been posted.
        """
        self.ensure_one()
        if self.move_type == 'in_refund':
            return
        purchase = self._get_linked_purchase_order()
        if not purchase or not purchase.use_separate_valuation:
            return
        existing_final = self._get_po_final_invoices(purchase)
        if existing_final:
            raise UserError(_(
                'Purchase order %s already has a final invoice (%s).\n'
                'No additional vendor bills can be posted for this order.'
            ) % (purchase.name, existing_final[0].name))

    # ------------------------------------------------------------------
    # Admin actions (Purchase Manager only)
    # ------------------------------------------------------------------

    def _check_purchase_manager(self):
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise UserError(_('Only Purchase Managers can change the Final Invoice status.'))

    def action_mark_as_final_invoice(self):
        """Mark a posted vendor bill as the Final Invoice.

        Available to Purchase Managers only.  Credit notes (in_refund) are
        intentionally excluded: a reversal document should not close the
        billing cycle.
        """
        self.ensure_one()
        self._check_purchase_manager()
        if self.state != 'posted':
            raise UserError(_('Only posted invoices can be marked as Final Invoice.'))
        if self.move_type not in _FINAL_INVOICE_TYPES:
            raise UserError(_('Only vendor bills can be marked as Final Invoice.'))
        if not self.po_use_separate_valuation:
            raise UserError(_(
                'The Final Invoice flag can only be set on vendor bills linked to a purchase '
                'order that uses Separate Valuation Mode.'
            ))
        self._check_no_existing_final_invoice()
        self._check_price_adjustment_account_configured()
        self.is_final_invoice = True

    def action_unmark_as_final_invoice(self):
        """Remove the Final Invoice flag from a posted vendor bill.

        Available to Purchase Managers only.
        """
        self.ensure_one()
        self._check_purchase_manager()
        if self.state != 'posted':
            raise UserError(_('Only posted invoices can be modified.'))
        self.is_final_invoice = False
