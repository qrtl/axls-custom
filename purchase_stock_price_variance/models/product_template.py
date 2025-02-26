# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    price_variance_threshold_percent = fields.Float(
        help="Maximum variance (in percent) allowable between the product's standard price"
        " and purchase receipt unit price. "
        "Setting this to zero means the threshold will refer to the global setting."
    )
    price_variance_threshold_amount = fields.Monetary(
        help="Maximum allowable variance (in monetary amount, based on company currency)"
        " between the product's standard price and the purchase receipt unit price. "
        "Setting this to zero means the threshold will refer to the global setting."
    )
    bypass_price_variance_check = fields.Boolean(
        copy=False,
        tracking=True,
        help="If enabled, this product will not be checked for price variance between "
        "the product's standard price and purchase receipt unit price.",
    )
    price_variance_threshold = fields.Boolean(
        compute="_compute_price_variance_threshold",
        store=True,
    )

    @api.depends("company_id", "company_id.price_variance_threshold")
    def _compute_price_variance_threshold(self):
        for product in self:
            product.price_variance_threshold = (
                product.company_id.price_variance_threshold
                if product.company_id
                else False
            )
