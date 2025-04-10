# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockProductRevaluationLine(models.Model):
    _name = 'stock.product.revaluation.line'
    _description = 'Stock Product Revaluation Line'

    revaluation_id = fields.Many2one('stock.product.revaluation', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number')
    account_id = fields.Many2one('account.account', string='Account')
    amount = fields.Float(string='Cost Adjustment')
