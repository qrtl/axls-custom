# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_VENDOR_BILL_TYPES = frozenset({'in_invoice', 'in_refund', 'in_receipt'})


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
        compute='_compute_price_adjustment_move_id',
        readonly=True,
    )
    po_has_other_final_invoice = fields.Boolean(
        string='PO Has Other Final Invoice',
        compute='_compute_po_has_other_final_invoice',
    )
    po_use_separate_valuation = fields.Boolean(
        string='PO Uses Separate Valuation',
        compute='_compute_po_use_separate_valuation',
        help='True when a linked purchase order uses separate valuation mode.',
    )

    @api.depends(
        'purchase_id',
        'purchase_id.use_separate_valuation',
        'invoice_line_ids.purchase_line_id.order_id',
        'invoice_line_ids.purchase_line_id.order_id.use_separate_valuation',
    )
    def _compute_po_use_separate_valuation(self):
        for move in self:
            move.po_use_separate_valuation = bool(
                move._get_linked_purchase_orders().filtered('use_separate_valuation')
            )

    @api.depends(
        'purchase_id',
        'invoice_line_ids.purchase_line_id.order_id',
        'purchase_id.final_invoice_move_id',
        'purchase_id.final_invoice_move_id.state',
        'invoice_line_ids.purchase_line_id.order_id.final_invoice_move_id',
        'invoice_line_ids.purchase_line_id.order_id.final_invoice_move_id.state',
        'invoice_line_ids.purchase_line_id.order_id.order_line.invoice_lines.move_id.is_final_invoice',
        'invoice_line_ids.purchase_line_id.order_id.order_line.invoice_lines.move_id.state',
    )
    def _compute_po_has_other_final_invoice(self):
        for move in self:
            move.po_has_other_final_invoice = any(
                purchase._get_final_invoice() and purchase._get_final_invoice() != move
                for purchase in move._get_linked_purchase_orders().filtered('use_separate_valuation')
            )

    @api.depends(
        'purchase_id',
        'invoice_line_ids.purchase_line_id.order_id',
        'purchase_id.price_adjustment_move_id',
        'purchase_id.final_invoice_move_id',
        'invoice_line_ids.purchase_line_id.order_id.price_adjustment_move_id',
        'invoice_line_ids.purchase_line_id.order_id.final_invoice_move_id',
    )
    def _compute_price_adjustment_move_id(self):
        for move in self:
            adjustment_move = self.env['account.move']
            for purchase in move._get_linked_purchase_orders().filtered('use_separate_valuation'):
                if purchase._get_final_invoice() == move:
                    adjustment_move = purchase.price_adjustment_move_id
                    break
            move.price_adjustment_move_id = adjustment_move[:1]

    def _post(self, soft=True):
        to_post = self.filtered(lambda m: m.state == 'draft') if soft else self

        for bill in to_post.filtered(lambda m: m.move_type in _VENDOR_BILL_TYPES):
            purchases = bill._get_separate_valuation_purchase_orders()
            if bill.is_final_invoice:
                purchase = bill._get_final_invoice_purchase_order()
                purchase._check_can_assign_final_invoice(bill, require_posted=False)
                purchase._check_price_adjustment_account_configured()
            elif bill.move_type != 'in_refund':
                for purchase in purchases:
                    purchase._check_no_bill_after_final_invoice(bill)

        result = super()._post(soft)

        purchases_to_sync = self.env['purchase.order']
        already_synced = self.env['purchase.order']
        for bill in result.filtered(lambda m: m.move_type in _VENDOR_BILL_TYPES):
            purchases_to_sync |= bill._get_separate_valuation_purchase_orders()

        for bill in result.filtered(
            lambda m: m.is_final_invoice and m.move_type in _VENDOR_BILL_TYPES
        ):
            purchase = bill._get_final_invoice_purchase_order(raise_if_missing=False)
            if purchase:
                purchase._set_final_invoice(bill)
                already_synced |= purchase

        for purchase in purchases_to_sync - already_synced:
            purchase._sync_price_adjustment_entry()

        return result

    def write(self, vals):
        track_final_flag = 'is_final_invoice' in vals
        track_purchase_link = 'purchase_id' in vals

        purchases_before = {}
        if track_final_flag or track_purchase_link:
            for move in self.filtered(lambda m: m.move_type in _VENDOR_BILL_TYPES):
                purchases_before[move.id] = move._get_linked_purchase_orders().filtered(
                    'use_separate_valuation'
                )

        res = super().write(vals)
        if self.env.context.get('skip_purchase_final_invoice_sync'):
            return res

        if track_final_flag:
            for move in self.filtered(
                lambda m: m.state == 'posted' and m.move_type in _VENDOR_BILL_TYPES
            ):
                if move.is_final_invoice:
                    purchase = move._get_final_invoice_purchase_order()
                    purchase._set_final_invoice(move)
                    continue

                for old_purchase in purchases_before.get(move.id, self.env['purchase.order']):
                    if old_purchase._get_final_invoice() == move or old_purchase.final_invoice_move_id == move:
                        old_purchase._clear_final_invoice(invoice=move)
        elif track_purchase_link:
            purchases_to_sync = self.env['purchase.order']
            for move in self.filtered(
                lambda m: m.state == 'posted' and m.move_type in _VENDOR_BILL_TYPES
            ):
                purchases_to_sync |= purchases_before.get(move.id, self.env['purchase.order'])
                purchases_to_sync |= move._get_separate_valuation_purchase_orders()
            for purchase in purchases_to_sync.filtered('use_separate_valuation'):
                purchase._sync_price_adjustment_entry()

        return res

    def button_draft(self):
        vendor_bills = self.filtered(lambda m: m.move_type in _VENDOR_BILL_TYPES)
        purchases_before = {
            move.id: move._get_separate_valuation_purchase_orders()
            for move in vendor_bills
        }
        final_purchases_before = {
            move.id: purchases_before[move.id].filtered(lambda po, move=move: po._get_final_invoice() == move)
            for move in vendor_bills
        }

        result = super().button_draft()
        if self.env.context.get('skip_purchase_final_invoice_sync'):
            return result

        to_sync = self.env['purchase.order']
        cleared = self.env['purchase.order']
        for move in vendor_bills:
            to_sync |= purchases_before[move.id]
            to_sync |= move._get_separate_valuation_purchase_orders()
            for purchase in final_purchases_before[move.id]:
                purchase._clear_final_invoice(invoice=move)
                cleared |= purchase

        for purchase in (to_sync - cleared).filtered('use_separate_valuation'):
            purchase._sync_price_adjustment_entry()
        return result

    def button_cancel(self):
        vendor_bills = self.filtered(lambda m: m.move_type in _VENDOR_BILL_TYPES)
        purchases_before = {
            move.id: move._get_separate_valuation_purchase_orders()
            for move in vendor_bills
        }
        final_purchases_before = {
            move.id: purchases_before[move.id].filtered(lambda po, move=move: po._get_final_invoice() == move)
            for move in vendor_bills
        }

        result = super().button_cancel()
        if self.env.context.get('skip_purchase_final_invoice_sync'):
            return result

        to_sync = self.env['purchase.order']
        cleared = self.env['purchase.order']
        for move in vendor_bills:
            to_sync |= purchases_before[move.id]
            to_sync |= move._get_separate_valuation_purchase_orders()
            for purchase in final_purchases_before[move.id]:
                purchase._clear_final_invoice(invoice=move)
                cleared |= purchase

        for purchase in (to_sync - cleared).filtered('use_separate_valuation'):
            purchase._sync_price_adjustment_entry()
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_linked_purchase_orders(self):
        self.ensure_one()
        return self.purchase_id | self.invoice_line_ids.mapped('purchase_line_id.order_id')

    def _get_separate_valuation_purchase_orders(self):
        self.ensure_one()
        return self._get_linked_purchase_orders().filtered('use_separate_valuation')

    def _get_final_invoice_purchase_order(self, raise_if_missing=True):
        self.ensure_one()
        purchases = self._get_separate_valuation_purchase_orders()
        if not purchases:
            if raise_if_missing:
                raise UserError(_(
                    'The Final Invoice flag can only be used on vendor bills linked to a '
                    'purchase order that uses Separate Valuation Mode.'
                ))
            return self.env['purchase.order']
        if len(purchases) > 1:
            raise UserError(_(
                'Final Invoice is only supported on vendor bills linked to a single '
                'Separate Valuation purchase order.'
            ))
        return purchases

    def _sync_price_adjustment_entry(self):
        self.ensure_one()
        purchase = self._get_final_invoice_purchase_order(raise_if_missing=False)
        if purchase:
            purchase._sync_price_adjustment_entry()

    # ------------------------------------------------------------------
    # Admin actions (Purchase Manager only)
    # ------------------------------------------------------------------

    def _check_purchase_manager(self):
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise UserError(_('Only Purchase Managers can change the Final Invoice status.'))

    def action_mark_as_final_invoice(self):
        self.ensure_one()
        self._check_purchase_manager()
        purchase = self._get_final_invoice_purchase_order()
        purchase._set_final_invoice(self)

    def action_unmark_as_final_invoice(self):
        self.ensure_one()
        self._check_purchase_manager()
        if self.state != 'posted':
            raise UserError(_('Only posted invoices can be modified.'))
        purchase = self._get_final_invoice_purchase_order(raise_if_missing=False)
        if purchase and purchase._get_final_invoice() == self:
            purchase._clear_final_invoice(invoice=self)
        elif self.is_final_invoice:
            self.with_context(skip_purchase_final_invoice_sync=True).write({
                'is_final_invoice': False,
            })
