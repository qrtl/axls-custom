# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, models


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
        if not args:
            args = []
        if name:
            new_args = [
                "|",
                ("name", operator, name),
                ("product_id.default_code", operator, name),
            ]
            lot_ids = list(
                self._search(
                    new_args + args, limit=limit, access_rights_uid=name_get_uid
                )
            )
            if not lot_ids:
                ptrn = re.compile(r"(\[(.*?)\])")
                res = ptrn.search(name)
                lot_name = name.replace("[" + res.group(2) + "] ", "")
                if res:
                    lot_ids = list(
                        self._search(
                            [
                                ("product_id.default_code", "=", res.group(2)),
                                ("name", operator, lot_name),
                            ]
                            + args,
                            limit=limit,
                            access_rights_uid=name_get_uid,
                        )
                    )
        else:
            lot_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return lot_ids
