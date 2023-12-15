# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    shelfinfo_id = fields.Many2one(
        "product.shelfinfo",
        string="Shelf Info.",
        compute="_compute_shelfinfo",
        store=True,
    )

    @api.depends("product_id", "product_id.shelfinfo_ids", "location_id")
    def _compute_shelfinfo(self):
        for rec in self:
            rec.shelfinfo_id = False
            location = rec.location_id
            if location.usage != "internal":
                continue
            rec.shelfinfo_id = self.env["product.shelfinfo"].search(
                [
                    ("product_id", "=", rec.product_id.id),
                    ("location_id", "=", location.id),
                ],
                limit=1,
            )
