# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.product"

    last_purchase_date = fields.Date(compute="_compute_last_purchase_date", store=True)

    @api.depends("stock_move_ids.state", "product_tmpl_id.last_purchase_date")
    def _compute_last_purchase_date(self):
        products = self.filtered(
            lambda p: p.type != "service" and p.allow_manual_purchase_date is False
        )
        moves = products.stock_move_ids.filtered(
            lambda m: m.state == "done" and m.picking_type_id.code == "incoming"
        )
        for move in moves:
            move.product_id.write({"last_purchase_date": move.date})
