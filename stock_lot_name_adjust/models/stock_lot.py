# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import models, api


class StockLot(models.Model):
    _inherit = "stock.lot"
    _rec_names_search = ["name", "product_id.default_code"]

    def name_get(self):
        name_list = []
        for rec in self:
            default_code = rec.product_id.default_code
            name = rec.name
            if default_code:
                name = "[%s] %s" % (default_code, name)
            name_list.append((rec.id, name))
        return name_list

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = []
        if name:
            lot_ids = list(self._search(args, limit=limit, access_rights_uid=name_get_uid))
            args += [
                "|",
                ("name", operator, name),
                ("product_id.default_code", operator, name),
            ]
            if not lot_ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    lot_ids = list(self._search([('default_code', '=', res.group(2))] + args, limit=limit, access_rights_uid=name_get_uid))
        return lot_ids
