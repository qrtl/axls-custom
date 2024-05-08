# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        if "|" not in name:
            return super().name_search(name, args, operator, limit)
        product_name, lot_name = name.split("|", 1)
        product = self.env["product.product"].search(
            [("name", "=", product_name)], limit=1
        )
        args += [("product_id", "=", product.id), ("name", operator, lot_name)]
        lot_ids = self._search(args, limit=limit)
        return self.browse(lot_ids).name_get()
