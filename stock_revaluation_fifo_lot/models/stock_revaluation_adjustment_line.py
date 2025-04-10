# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockRevaluationAdjustmentLine(models.Model):
    _name = 'stock.product.revaluation.valuation'
    _description = 'Stock Product Revaluation Valuation'

    revaluation_id = fields.Many2one('stock.product.revaluation', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number')
    original_value = fields.Float(string='Original Value')
    new_value = fields.Float(string='New Value')
    difference = fields.Float(string='Difference', compute='_compute_difference', store=True)

    @api.depends('original_value', 'new_value')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.new_value - rec.original_value