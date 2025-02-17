# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    price_variance_threshold_percent = fields.Float(
        help="Maximum variance (in percent) allowable between the product's standard price"
        " and purchase receipt unit price."
    )
    price_variance_threshold_amount = fields.Float(
        help="Maximum allowable variance (in monetary amount, based on company currency)"
        " between the product's standard price and the purchase receipt unit price."
    )
