# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = "product.category"

    enable_specific_identification_method = fields.Boolean(
        compute="_compute_enable_specific_identification_method",
        readonly=False,
        store=True,
    )
    category_cost_method = fields.Selection(
        [
            ("standard", "Standard Price"),
            ("fifo", "First In First Out (FIFO)"),
            ("average", "Average Cost (AVCO)"),
            ("specific_identification", "Specific Identification"),
        ],
        string="Category Costing Method",
        compute="_compute_category_cost_method",
    )

    @api.depends("property_cost_method")
    def _compute_enable_specific_identification_method(self):
        for rec in self:
            if rec.property_cost_method != "fifo":
                rec.enable_specific_identification_method = False

    @api.depends("enable_specific_identification_method", "property_cost_method")
    def _compute_category_cost_method(self):
        for rec in self:
            if (
                rec.enable_specific_identification_method
                and rec.property_cost_method == "fifo"
            ):
                rec.category_cost_method = "specific_identification"
                continue
            rec.category_cost_method = rec.property_cost_method

    @api.constrains("enable_specific_identification_method")
    def _check_enable_specific_identification_method(self):
        for rec in self:
            if not (
                rec.enable_specific_identification_method
                and rec.property_cost_method == "fifo"
            ):
                continue
            products = self.env["product.template"].search(
                [("categ_id", "=", rec.id), ("tracking", "=", "none")]
            )
            if not products:
                continue
            product_names = "\n - ".join(p.name for p in products)
            raise ValidationError(
                _(
                    "You cannot enable Specific Identification Method for this category "
                    "because the following products do not have serial or lot "
                    "tracking:\n - %s"
                )
                % product_names
            )
