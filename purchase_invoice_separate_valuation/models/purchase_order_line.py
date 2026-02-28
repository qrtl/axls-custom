# -*- coding: utf-8 -*-
from odoo import api, fields, models


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
        """Compute invoiced amount from ALL posted vendor bills (both partial and final).

        This tracks the actual money invoiced, independent of the qty-based tracking.
        """
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
                if move.move_type in ('in_invoice', 'in_receipt'):
                    amount = inv_line.price_subtotal
                else:
                    amount = -inv_line.price_subtotal
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

    @api.depends(
        'invoice_lines.move_id.state',
        'invoice_lines.move_id.is_final_invoice',
        'invoice_lines.quantity',
        'qty_received',
        'product_uom_qty',
        'order_id.state',
        'order_id.use_separate_valuation',
    )
    def _compute_qty_invoiced(self):
        """Override qty_invoiced computation.

        For regular orders (use_separate_valuation=False): standard Odoo behaviour.
        For separate-valuation orders:
          - Before final invoice: qty_invoiced=0, qty_to_invoice=full pending qty.
          - After a POSTED final invoice: qty_invoiced=full qty, qty_to_invoice=0,
            which closes the purchase order's billing status.
        """
        separate_lines = self.filtered(lambda l: l.order_id.use_separate_valuation)
        regular_lines = self - separate_lines
        if regular_lines:
            super(PurchaseOrderLine, regular_lines)._compute_qty_invoiced()
        for line in separate_lines:
            if line.order_id.state not in ('purchase', 'done'):
                line.qty_invoiced = 0.0
                line.qty_to_invoice = 0.0
                continue
            has_final_invoice = any(
                inv_line.move_id.state == 'posted'
                and inv_line.move_id.is_final_invoice
                for inv_line in line._get_invoice_lines()
                if inv_line.move_id.move_type in ('in_invoice', 'in_refund', 'in_receipt')
            )
            basis_qty = (
                line.product_qty
                if line.product_id.purchase_method == 'purchase'
                else line.qty_received
            )
            if has_final_invoice:
                line.qty_invoiced = basis_qty
                line.qty_to_invoice = 0.0
            else:
                line.qty_invoiced = 0.0
                line.qty_to_invoice = basis_qty
