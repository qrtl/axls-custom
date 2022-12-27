# Copyright 2022 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    esc_code = fields.Char(related="product_tmpl_id.esc_code")

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(["name", "default_code", "esc_code"])
        return [
            (
                template.id,
                "%s%s"
                % (
                    "[%s/%s] " % (template.default_code, template.esc_code or ""),
                    template.name,
                ),
            )
            for template in self
        ]

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
                ("esc_code", operator, name),
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
