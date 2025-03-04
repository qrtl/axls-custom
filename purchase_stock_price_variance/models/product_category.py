# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    bypass_price_variance_check = fields.Boolean(
        copy=False,
        tracking=True,
        help="If enabled, this products under this category will not be checked for "
        "price variance between the product's standard price and purchase receipt unit price.",
    )

    enable_price_variance_error = fields.Boolean(
        compute="_compute_enable_price_variance_error",
    )

    @api.depends_context("company")
    def _compute_enable_price_variance_error(self):
        company = self.env.company
        for rec in self:
            rec.enable_price_variance_error = company.enable_price_variance_error
