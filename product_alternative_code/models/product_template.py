# Copyright 2022 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alt_code = fields.Char("Alternative Code", help="Alternative product code.")

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
