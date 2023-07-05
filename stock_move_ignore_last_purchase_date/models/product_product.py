# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends("stock_move_ids.state", "man_last_purchase_date")
    def _compute_last_purchase_date(self):
        for product in self:
            last_purchase_date = False
            man_last_purchase_date = product.man_last_purchase_date
            move = product.stock_move_ids.filtered(
                lambda m: m.state == "done" and m.picking_code == "incoming"
            ).sorted(key=lambda m: m.id, reverse=True)[:1]
            if move:
                if move.ignore_last_purchase_date and man_last_purchase_date:
                    last_purchase_date = man_last_purchase_date
                else:
                    last_purchase_date = fields.Date.context_today(self, move.date)
            if (
                not last_purchase_date
                or man_last_purchase_date
                and man_last_purchase_date > last_purchase_date
            ):
                last_purchase_date = man_last_purchase_date
            product.last_purchase_date = last_purchase_date
            product.product_tmpl_id._compute_last_purchase_date()
