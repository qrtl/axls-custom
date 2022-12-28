# Copyright 2022 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def name_get(self):
        res = super().name_get()
        name_list = []
        for rec in res:
            product = self.browse(rec[0])
            alt_code = product.alt_code
            if not alt_code:
                name_list.append(rec)
                continue
            name = rec[1]
            if not product.default_code:
                name = "[" + alt_code + "] " + name
                name_list.append((rec[0], name))
                continue
            pos = name.find("]")
            name = name[:pos] + "/" + alt_code + name[pos:]
            name_list.append((rec[0], name))
        return name_list

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = list(args or [])
        if name:
            args += [
                "|",
                "|",
                ("name", operator, name),
                ("alt_code", operator, name),
                ("default_code", operator, name),
            ]
        product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        if not product_ids:
            product_ids = super()._name_search(
                name=name,
                args=args,
                operator=operator,
                limit=limit,
                name_get_uid=name_get_uid,
            )
        return product_ids
