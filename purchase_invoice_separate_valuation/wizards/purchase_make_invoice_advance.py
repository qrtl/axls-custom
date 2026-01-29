# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseMakeInvoiceAdvance(models.TransientModel):
    _name = 'purchase.make_invoice_advance'
    _description = 'Create Invoice from Purchase Order'

    is_final_invoice = fields.Boolean(
        string='Final Invoice',
        default=False,
        help='Mark this as the final invoice. This will update purchase order quantities and close the order.'
    )
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Purchase Orders',
        required=True
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            res['purchase_order_ids'] = [(6, 0, active_ids)]
        return res

    def create_invoice(self):
        """Create invoice from purchase orders"""
        if not self.purchase_order_ids:
            raise UserError(_('Please select at least one purchase order.'))

        invoices = self.env['account.move']
        for purchase_order in self.purchase_order_ids:
            if purchase_order.state not in ['purchase', 'done']:
                raise UserError(_('You can only create invoices from confirmed purchase orders.'))

            # Use the standard purchase order invoice creation method
            # but with our custom context
            ctx = self.env.context.copy()
            ctx.update({
                'final_invoice': self.is_final_invoice,
            })
            
            # Create invoice with standard method
            invoice_vals = purchase_order.with_context(ctx)._prepare_invoice()
            invoice_vals['is_final_invoice'] = self.is_final_invoice
            
            # Create invoice with lines in one operation
            lines_vals = []
            for line in purchase_order.order_line:
                if line.display_type:
                    continue
                    
                # Determine quantity to invoice
                if self.is_final_invoice:
                    qty_to_invoice = line.qty_to_invoice
                else:
                    # Allow invoicing any quantity for non-final invoices
                    if line.product_id.purchase_method == 'purchase':
                        qty_to_invoice = line.product_qty - (line.qty_invoiced if self.is_final_invoice else 0)
                    else:
                        qty_to_invoice = line.qty_received - (line.qty_invoiced if self.is_final_invoice else 0)

                if qty_to_invoice > 0:
                    line_vals = line._prepare_account_move_line(
                        self.env['account.move'].with_context(ctx).new(invoice_vals)
                    )
                    line_vals['quantity'] = qty_to_invoice
                    lines_vals.append((0, 0, line_vals))
            
            # Add lines to invoice vals
            invoice_vals['invoice_line_ids'] = lines_vals
            
            # Create the complete invoice
            invoice = self.env['account.move'].create(invoice_vals)
            invoices |= invoice

        # Return action to view created invoices
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bills'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'target': 'current',
        }
        
        if len(invoices) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
            
        return action