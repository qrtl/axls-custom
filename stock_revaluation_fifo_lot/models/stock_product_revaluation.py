# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockProductRevaluation(models.Model):
    _name = 'stock.product.revaluation'
    _description = 'Stock Product Revaluation'
    _order = 'date desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('stock.product.revaluation'))
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    line_ids = fields.One2many('stock.product.revaluation.line', 'revaluation_id', string='Revaluation Lines')
    valuation_adjustment_ids = fields.One2many('stock.revaluation.adjustment.line', 'revaluation_id', string='Valuation Adjustments')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)

    def action_post(self):
        for record in self:
            if not record.line_ids:
                raise UserError("Please add at least one revaluation line.")

            # Example placeholder for valuation calculation logic
            for line in record.line_ids:
                # Simulate retrieving old valuation and calculating new one
                original_value = 100  # Placeholder
                new_value = original_value + line.amount

                self.env['stock.product.revaluation.valuation'].create({
                    'revaluation_id': record.id,
                    'product_id': line.product_id.id,
                    'lot_id': line.lot_id.id,
                    'original_value': original_value,
                    'new_value': new_value,
                    'difference': new_value - original_value,
                })

            record.state = 'posted'
