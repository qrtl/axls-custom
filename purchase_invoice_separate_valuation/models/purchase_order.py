# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_VENDOR_BILL_TYPES = frozenset({'in_invoice', 'in_refund', 'in_receipt'})
_FINAL_INVOICE_TYPES = frozenset({'in_invoice', 'in_receipt'})


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    use_separate_valuation = fields.Boolean(
        string='Separate Valuation Mode',
        default=False,
        copy=False,
        readonly=True,
        help='Set automatically when invoices are created via "Create Invoice (Advanced)". '
             'When active, the standard "Create Invoice" button is blocked and invoicing '
             'is managed separately from stock valuation.',
    )
    price_diff_reason = fields.Text(
        string='Price Difference Note',
        help='Reason for any difference between the receipt value and the invoiced amount.',
    )
    amount_invoiced = fields.Monetary(
        string='Invoiced Amount',
        compute='_compute_amount_invoiced',
        store=True,
        currency_field='currency_id',
    )
    amount_to_invoice = fields.Monetary(
        string='Amount to Invoice',
        compute='_compute_amount_invoiced',
        store=True,
        currency_field='currency_id',
    )
    has_final_invoice = fields.Boolean(
        string='Has Final Invoice',
        compute='_compute_has_final_invoice',
    )
    final_invoice_move_id = fields.Many2one(
        'account.move',
        string='Final Invoice',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    price_adjustment_move_id = fields.Many2one(
        'account.move',
        string='Price Adjustment Entry',
        readonly=True,
        copy=False,
        ondelete='set null',
    )

    @api.depends(
        'final_invoice_move_id',
        'final_invoice_move_id.state',
        'final_invoice_move_id.move_type',
        'order_line.invoice_lines.move_id.is_final_invoice',
        'order_line.invoice_lines.move_id.state',
        'order_line.invoice_lines.move_id.move_type',
    )
    def _compute_has_final_invoice(self):
        for order in self:
            order.has_final_invoice = bool(order._get_final_invoice())

    @api.depends('order_line.amount_invoiced', 'amount_untaxed', 'currency_id')
    def _compute_amount_invoiced(self):
        for order in self:
            total = sum(order.order_line.mapped('amount_invoiced'))
            order.amount_invoiced = total
            order.amount_to_invoice = order.amount_untaxed - total

    def action_create_invoice(self):
        """Block standard invoice creation for orders using separate valuation mode."""
        blocked = self.filtered('use_separate_valuation')
        if blocked:
            names = ', '.join(blocked.mapped('name'))
            raise UserError(_(
                'The following purchase order(s) use Separate Valuation Mode:\n%s\n\n'
                'Please use the "Create Invoice (Advanced)" button instead.'
            ) % names)
        return super().action_create_invoice()

    # ------------------------------------------------------------------
    # Separate valuation helpers
    # ------------------------------------------------------------------

    def _get_vendor_bills(self):
        self.ensure_one()
        return self.order_line.mapped('invoice_lines.move_id').filtered(
            lambda m: m.move_type in _VENDOR_BILL_TYPES
        )

    def _get_final_invoice(self):
        self.ensure_one()
        final_invoice = self.final_invoice_move_id
        if final_invoice and final_invoice.state == 'posted' and final_invoice.move_type in _FINAL_INVOICE_TYPES:
            return final_invoice
        legacy_final = self._get_vendor_bills().filtered(
            lambda m: m.is_final_invoice
            and m.state == 'posted'
            and m.move_type in _FINAL_INVOICE_TYPES
        )
        return legacy_final[:1]

    def _check_can_create_advanced_invoice(self, is_final=False):
        self.ensure_one()
        if self.state not in ('purchase', 'done'):
            raise UserError(_(
                'You can only create invoices from confirmed purchase orders.'
            ))

        existing_bills = self._get_vendor_bills().filtered(lambda m: m.state != 'cancel')
        if not self.use_separate_valuation and existing_bills:
            raise UserError(_(
                'Purchase order %s already has vendor bills.\n'
                'Separate Valuation Mode must be started before any vendor bill is created.'
            ) % self.name)

        existing_final = self._get_final_invoice()
        if existing_final:
            raise UserError(_(
                'Purchase order %s already has a final invoice (%s).\n'
                'Clear the Final Invoice status before creating another bill.'
            ) % (self.name, existing_final.display_name or existing_final.name))

    def _check_no_bill_after_final_invoice(self, bill=None):
        self.ensure_one()
        if bill and bill.move_type == 'in_refund':
            return
        if not self.use_separate_valuation:
            return
        existing_final = self._get_final_invoice()
        if existing_final and existing_final != bill:
            raise UserError(_(
                'Purchase order %s already has a final invoice (%s).\n'
                'No additional vendor bills can be posted for this order.'
            ) % (self.name, existing_final.display_name or existing_final.name))

    def _check_can_assign_final_invoice(self, invoice, require_posted=True):
        self.ensure_one()
        if require_posted and invoice.state != 'posted':
            raise UserError(_('Only posted invoices can be marked as Final Invoice.'))
        if invoice.move_type not in _FINAL_INVOICE_TYPES:
            raise UserError(_('Only vendor bills can be marked as Final Invoice.'))
        if not self.use_separate_valuation:
            raise UserError(_(
                'The Final Invoice flag can only be set on vendor bills linked to a purchase '
                'order that uses Separate Valuation Mode.'
            ))
        if invoice not in self._get_vendor_bills():
            raise UserError(_(
                'Invoice %s is not linked to purchase order %s.'
            ) % (invoice.display_name or invoice.name, self.name))
        existing_final = self._get_final_invoice()
        if existing_final and existing_final != invoice:
            raise UserError(_(
                'Purchase order %s already has a final invoice (%s).\n'
                'Please remove the existing final invoice status first.'
            ) % (self.name, existing_final.display_name or existing_final.name))

    def _set_final_invoice(self, invoice):
        self.ensure_one()
        self._check_can_assign_final_invoice(invoice)

        current_final = self._get_final_invoice()
        if current_final and current_final != invoice and current_final.is_final_invoice:
            current_final.with_context(skip_purchase_final_invoice_sync=True).write({
                'is_final_invoice': False,
            })

        if self.final_invoice_move_id != invoice:
            self.write({'final_invoice_move_id': invoice.id})
        if not invoice.is_final_invoice:
            invoice.with_context(skip_purchase_final_invoice_sync=True).write({
                'is_final_invoice': True,
            })

        self._sync_price_adjustment_entry()

    def _clear_final_invoice(self, invoice=None):
        self.ensure_one()
        current_final = self._get_final_invoice()
        if invoice and current_final and current_final != invoice:
            raise UserError(_(
                'Invoice %s is not the current Final Invoice for purchase order %s.'
            ) % (invoice.display_name or invoice.name, self.name))

        invoice_to_clear = current_final or invoice
        if self.final_invoice_move_id:
            self.write({'final_invoice_move_id': False})
        if invoice_to_clear and invoice_to_clear.is_final_invoice:
            invoice_to_clear.with_context(skip_purchase_final_invoice_sync=True).write({
                'is_final_invoice': False,
            })

        self._sync_price_adjustment_entry()

    def _get_purchase_stock_input_account_ids(self):
        self.ensure_one()
        account_ids = set()
        for line in self.order_line.filtered('product_id'):
            account = line.product_id.product_tmpl_id._get_product_accounts().get('stock_input')
            if account:
                account_ids.add(account.id)
        return account_ids

    def _check_price_adjustment_account_configured(self, stock_input_account_ids=None):
        self.ensure_one()
        account_ids = stock_input_account_ids
        if account_ids is None:
            account_ids = self._get_purchase_stock_input_account_ids()
        if account_ids and not self.company_id.purchase_price_adjustment_account_id:
            final_invoice = self._get_final_invoice()
            raise UserError(_(
                'Please configure "Purchase Price Adjustment Account" in Accounting settings '
                'before posting Final Invoice %s.'
            ) % (final_invoice.display_name or final_invoice.name or self.name))

    def _grni_line_vals(self, invoice, account_id, debit=0.0, credit=0.0):
        return {
            'name': _('GRNI adjustment (Final Invoice %s)') % (invoice.name or invoice.display_name),
            'account_id': account_id,
            'debit': debit,
            'credit': credit,
            'partner_id': invoice.partner_id.id,
        }

    def _remove_price_adjustment_entry(self):
        self.ensure_one()
        adj = self.price_adjustment_move_id
        if not adj:
            return
        try:
            if adj.state == 'posted':
                adj.button_draft()
            adj.unlink()
        except Exception as err:
            raise UserError(_(
                'Could not remove the GRNI adjustment entry %s.\n'
                'Please unreconcile or manually reverse it first.\n\nDetail: %s'
            ) % (adj.name, str(err))) from err
        self.write({'price_adjustment_move_id': False})

    def _sync_price_adjustment_entry(self):
        for order in self:
            order._sync_price_adjustment_entry_one()

    def _sync_price_adjustment_entry_one(self):
        self.ensure_one()

        final_invoice = self._get_final_invoice()
        if final_invoice and self.final_invoice_move_id != final_invoice:
            self.write({'final_invoice_move_id': final_invoice.id})

        if (
            not final_invoice
            or final_invoice.state != 'posted'
            or final_invoice.move_type not in _FINAL_INVOICE_TYPES
        ):
            if self.price_adjustment_move_id:
                self._remove_price_adjustment_entry()
            return

        stock_input_account_ids = self._get_purchase_stock_input_account_ids()
        if not stock_input_account_ids:
            if self.price_adjustment_move_id:
                self._remove_price_adjustment_entry()
            return

        self._check_price_adjustment_account_configured(
            stock_input_account_ids=stock_input_account_ids,
        )
        price_adjustment_account = self.company_id.purchase_price_adjustment_account_id

        grni_journal = self.company_id.purchase_grni_adjustment_journal_id
        if not grni_journal:
            grni_journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        if not grni_journal:
            raise UserError(_(
                'Please configure a GRNI Adjustment Journal for company %s before '
                'finalising purchase order %s.'
            ) % (self.company_id.display_name, self.display_name))

        done_moves = self.order_line.mapped('move_ids').filtered(
            lambda m: m.state == 'done'
            and m.product_id
            and m.product_id.type == 'product'
            and m.product_id.categ_id.property_valuation == 'real_time'
        )
        receipt_balances = {}
        for aml in done_moves.mapped('account_move_ids.line_ids').filtered(
            lambda l: l.account_id.id in stock_input_account_ids and l.move_id.state == 'posted'
        ):
            receipt_balances.setdefault(aml.account_id.id, 0.0)
            receipt_balances[aml.account_id.id] += aml.balance

        posted_bills = self._get_vendor_bills().filtered(lambda m: m.state == 'posted')
        invoice_balances = {}
        if posted_bills:
            for aml in self.env['account.move.line'].search([
                ('move_id', 'in', posted_bills.ids),
                ('account_id', 'in', list(stock_input_account_ids)),
            ]):
                invoice_balances.setdefault(aml.account_id.id, 0.0)
                invoice_balances[aml.account_id.id] += aml.balance

        adjustment_lines = []
        precision_rounding = self.company_id.currency_id.rounding
        for account_id in set(receipt_balances) | set(invoice_balances):
            total_balance = (
                receipt_balances.get(account_id, 0.0)
                + invoice_balances.get(account_id, 0.0)
            )
            if float_is_zero(total_balance, precision_rounding=precision_rounding):
                continue

            amount = abs(total_balance)
            if total_balance > 0:
                adjustment_lines += [
                    self._grni_line_vals(final_invoice, price_adjustment_account.id, debit=amount),
                    self._grni_line_vals(final_invoice, account_id, credit=amount),
                ]
            else:
                adjustment_lines += [
                    self._grni_line_vals(final_invoice, account_id, debit=amount),
                    self._grni_line_vals(final_invoice, price_adjustment_account.id, credit=amount),
                ]

        if adjustment_lines:
            if self.price_adjustment_move_id:
                self._remove_price_adjustment_entry()

            adjustment_move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': grni_journal.id,
                'date': final_invoice.date,
                'ref': _('GRNI Adjustment - Final Invoice %s') % (final_invoice.name or final_invoice.display_name),
                'line_ids': [(0, 0, vals) for vals in adjustment_lines],
            })
            adjustment_move.action_post()
            self.write({'price_adjustment_move_id': adjustment_move.id})
        elif self.price_adjustment_move_id:
            self._remove_price_adjustment_entry()
