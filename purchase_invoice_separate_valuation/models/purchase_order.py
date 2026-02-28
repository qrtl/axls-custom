# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


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

    @api.depends(
        'order_line.invoice_lines.move_id.is_final_invoice',
        'order_line.invoice_lines.move_id.state',
        'order_line.invoice_lines.move_id.move_type',
    )
    def _compute_has_final_invoice(self):
        for order in self:
            order.has_final_invoice = bool(
                order.order_line.mapped('invoice_lines.move_id').filtered(
                    lambda m: m.is_final_invoice
                    and m.state == 'posted'
                    and m.move_type in ('in_invoice', 'in_refund', 'in_receipt')
                )
            )

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
