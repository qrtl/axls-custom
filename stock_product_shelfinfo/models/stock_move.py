# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    shelfinfo_src_id = fields.Many2one(
        "product.shelfinfo",
        string="Shelf Info. (From)",
        compute="_compute_shelfinfo",
        store=True,
    )
    shelfinfo_dest_id = fields.Many2one(
        "product.shelfinfo",
        string="Shelf Info. (To)",
        compute="_compute_shelfinfo",
        store=True,
    )

    @api.depends("product_id", "location_id", "location_dest_id")
    def _compute_shelfinfo(self):
        for move in self:
            move.shelfinfo_src_id = False
            move.shelfinfo_dest_id = False
            loc_src = move.location_id
            loc_dest = move.location_dest_id
            for shelfinfo in move.product_id.shelfinfo_ids:
                if loc_src.usage == "internal" and loc_src == shelfinfo.location_id:
                    move.shelfinfo_src_id = shelfinfo
                if loc_dest.usage == "internal" and loc_dest == shelfinfo.location_id:
                    move.shelfinfo_dest_id = shelfinfo
