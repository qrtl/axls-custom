# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

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

    @api.depends(
        'invoice_lines.move_id.state',
        'invoice_lines.price_subtotal',
        'invoice_lines.move_id.currency_id',
        'invoice_lines.move_id.invoice_date',
        'invoice_lines.move_id.move_type',
        'price_subtotal',
        'order_id.currency_id',
    )
    def _compute_amount_invoiced(self):
        for line in self:
            total = 0.0
            order = line.order_id
            if not order:
                line.amount_invoiced = 0.0
                line.amount_to_invoice = 0.0
                continue

            for inv_line in line._get_invoice_lines():
                move = inv_line.move_id
                if move.state != 'posted':
                    continue
                if move.move_type not in ('in_invoice', 'in_refund', 'in_receipt'):
                    continue
                amount = inv_line.price_subtotal * move.direction_sign
                if move.currency_id != order.currency_id:
                    amount = move.currency_id._convert(
                        amount,
                        order.currency_id,
                        line.company_id,
                        move.invoice_date or move.date or fields.Date.context_today(line),
                    )
                total += amount

            line.amount_invoiced = total
            line.amount_to_invoice = line.price_subtotal - total

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_received', 'product_uom_qty', 'order_id.state')
    def _compute_qty_invoiced(self):
        """Override to prevent qty_invoiced update unless final_invoice flag is set"""
        for line in self:
            # compute qty_invoiced only from final invoices
            qty = 0.0
            for inv_line in line._get_invoice_lines():
                if inv_line.move_id.state not in ['cancel'] or inv_line.move_id.payment_state == 'invoicing_legacy':
                    # Only count invoices marked as final_invoice
                    if inv_line.move_id.is_final_invoice:
                        if inv_line.move_id.move_type == 'in_invoice':
                            qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                        elif inv_line.move_id.move_type == 'in_refund':
                            qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
            line.qty_invoiced = qty

            # compute qty_to_invoice
            if line.order_id.state in ['purchase', 'done']:
                if line.product_id.purchase_method == 'purchase':
                    line.qty_to_invoice = line.product_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_received - line.qty_invoiced
            else:
                line.qty_to_invoice = 0


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

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

    @api.depends('order_line.amount_invoiced', 'amount_untaxed', 'currency_id')
    def _compute_amount_invoiced(self):
        for order in self:
            total = sum(order.order_line.mapped('amount_invoiced'))
            order.amount_invoiced = total
            order.amount_to_invoice = order.amount_untaxed - total
