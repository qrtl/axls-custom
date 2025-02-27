# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
    enable_price_variance_error = fields.Boolean(
        compute="_compute_enable_price_variance_error",
    )

    @api.depends("company_id")
    @api.depends_context("company")
    def _compute_enable_price_variance_error(self):
        for rec in self:
            company = rec.company_id or rec.env.company
            rec.enable_price_variance_error = (
                company.enable_price_variance_error if company else False
            )

    @api.constrains(
        "price_variance_threshold_percent", "price_variance_threshold_amount"
    )
    def _check_price_variance_threshold(self):
        for rec in self:
            if (
                rec.price_variance_threshold_percent < 0
                or rec.price_variance_threshold_amount < 0
            ):
                raise ValidationError(_("The threshold values cannot be negative."))
