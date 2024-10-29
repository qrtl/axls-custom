# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    quality_check_categ_code = fields.Char(
        string="Quality Check Categ. Code",
        compute="_compute_quality_check_category",
    )

    @api.depends("product_id", "picking_type_id")
    def _compute_quality_check_category(self):
        for move in self:
            move.quality_check_categ_code = False
            if move.picking_type_id.code == "incoming":
                move.quality_check_categ_code = (
                    move.product_id.quality_check_categ_id.code
                )
