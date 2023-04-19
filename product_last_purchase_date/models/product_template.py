# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    last_purchase_date = fields.Date(compute="_compute_last_purchase_date", store=True)
    man_last_purchase_date = fields.Date()
    allow_manual_purchase_date = fields.Boolean()

    @api.depends("product_variant_ids.last_purchase_date")
    def _compute_last_purchase_date(self):
        for template in self:
            if template.product_variant_ids:
                template.last_purchase_date = template.product_variant_ids[
                    0
                ].last_purchase_date
