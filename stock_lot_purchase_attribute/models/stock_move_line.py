# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    purchase_id = fields.Many2one(related="lot_id.purchase_id", store=True)
    purchase_partner_id = fields.Many2one(
        related="lot_id.purchase_partner_id", store=True
    )
