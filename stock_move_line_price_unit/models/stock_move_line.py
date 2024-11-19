# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    price_unit = fields.Float(related="move_id.price_unit", string="Unit Price")
