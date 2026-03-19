# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


class PurchaseMakeInvoiceAdvance(models.TransientModel):
    _name = 'purchase.make_invoice_advance'
    _description = 'Create Invoice from Purchase Order (Separate Valuation)'

    is_final_invoice = fields.Boolean(
        string='Final Invoice',
        default=False,
        help='Mark as the final invoice for this purchase order. '
             'This closes the billing cycle and triggers GRNI balancing.',
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        required=True,
    )

    @api.model
    def default_get(self, field_names):
        res = super().default_get(field_names)
        active_ids = self.env.context.get('active_ids', [])
        if len(active_ids) > 1:
            raise UserError(_(
                'Please open the purchase order form and use the '
                '"Create Invoice (Advanced)" button there. '
                'Only one purchase order can be invoiced at a time.'
            ))
        if active_ids:
            res['purchase_order_id'] = active_ids[0]
        return res

    def create_invoice(self):
        """Create a vendor bill for the selected purchase order.

        Quantity calculation always uses amount_to_invoice (money-based) so
        that fractional-quantity rounding never causes a discrepancy between
        what was already billed and what is proposed next time.

        Lines whose remaining amount is zero or negative are skipped entirely
        rather than creating zero-amount placeholder lines.
        """
        purchase_order = self.purchase_order_id
        if not purchase_order:
            raise UserError(_('Please select a purchase order.'))

        purchase_order._check_can_create_advanced_invoice(is_final=self.is_final_invoice)

        invoice_vals = purchase_order._prepare_invoice()
        invoice_vals['is_final_invoice'] = self.is_final_invoice

        lines_vals = []
        # Temporary record for _prepare_account_move_line
        tmp_move = self.env['account.move'].with_context(
            final_invoice=self.is_final_invoice
        ).new(invoice_vals)

        for line in purchase_order.order_line.filtered(lambda l: not l.display_type):
            line_vals = self._prepare_line_vals(line, tmp_move)
            if line_vals is None:
                continue
            lines_vals.append((0, 0, line_vals))

        if not lines_vals:
            raise UserError(_(
                'No remaining amount to invoice for %s. '
                'All lines have already been fully invoiced.'
            ) % purchase_order.name)

        invoice_vals['invoice_line_ids'] = lines_vals
        invoice = self.env['account.move'].create(invoice_vals)

        # Flag the purchase order as using separate-valuation mode
        if not purchase_order.use_separate_valuation:
            purchase_order.with_context(tracking_disable=True).write(
                {'use_separate_valuation': True}
            )

        return self._return_invoice_action(invoice)

    def _prepare_line_vals(self, line, tmp_move):
        """Return line_vals dict for a single PO line, or None to skip.

        Lines with a zero or negative remaining amount are skipped so that the
        invoice does not contain confusing zero-price rows.

        For lines with a positive remaining amount the invoice line is always
        created with qty=1 and price_unit=remaining_amount so that the invoice
        total is exact regardless of fractional product quantities.

        For products with price-inclusive taxes, amount_to_invoice is
        tax-exclusive (based on price_subtotal).  The invoice line's price_unit
        must be the tax-inclusive (gross) amount so that Odoo's tax engine
        computes the correct price_subtotal when it back-calculates.
        We achieve this by running compute_all on the inclusive taxes in
        price-exclusive mode (handle_price_include=False) to obtain the
        gross-up factor: price_unit = remaining_amount + inclusive_tax_amount.
        """
        remaining_amount = line.amount_to_invoice
        if (
            float_is_zero(remaining_amount, precision_rounding=line.currency_id.rounding)
            or remaining_amount <= 0
        ):
            return None
        line_vals = line._prepare_account_move_line(tmp_move)

        # Resolve tax IDs from ORM command format [(6, 0, [ids])]
        tax_ids = []
        for cmd in line_vals.get('tax_ids', []):
            if isinstance(cmd, (list, tuple)):
                if cmd[0] == 6:
                    tax_ids = list(cmd[2])
                elif cmd[0] == 4:
                    tax_ids.append(cmd[1])

        # For price-inclusive taxes, gross up to the tax-inclusive price_unit.
        include_taxes = self.env['account.tax'].browse(tax_ids).filtered('price_include')
        if include_taxes:
            tax_res = include_taxes.compute_all(
                remaining_amount,
                currency=line.currency_id,
                quantity=1.0,
                product=line.product_id,
                partner=line.order_id.partner_id,
                handle_price_include=False,
            )
            price_unit = tax_res['total_included']
        else:
            price_unit = remaining_amount

        line_vals['quantity'] = 1.0
        line_vals['discount'] = 0.0
        line_vals['price_unit'] = price_unit
        return line_vals

    @staticmethod
    def _return_invoice_action(invoice):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bills'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }
