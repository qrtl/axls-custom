# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    channel_category = fields.Char()
    lot_suffix = fields.Char()

    def name_get(self):
        name_list = super().name_get()
        new_name_list = []
        for name in name_list:
            rec = self.browse(name[0])
            new_name = name[1]
            if rec.lot_suffix:
                new_name += "-" + rec.lot_suffix
            if rec.channel_category:
                new_name += "-" + rec.channel_category
            new_name_list.append((name[0], new_name))
        return new_name_list
