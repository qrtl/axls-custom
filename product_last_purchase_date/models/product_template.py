# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    man_last_purchase_date = fields.Date(
        "Last Purchase Date (Man.)",
        compute="_compute_last_purchase_date",
        inverse="_inverse_man_last_purchase_date",
        store=True,
        copy=False,
        help="Update this field to force set Last Purchase Date in absence of past "
        "receipt records. If there is a receipt record dated after this date, the date "
        "of the receipt prevails.",
    )
    last_purchase_date = fields.Date(
        compute="_compute_last_purchase_date",
        store=True,
        help="Date of the last receipt from the supplier.",
    )

    @api.depends(
        "product_variant_ids",
        "product_variant_ids.man_last_purchase_date",
        "product_variant_ids.last_purchase_date",
    )
    def _compute_last_purchase_date(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.man_last_purchase_date = (
                template.product_variant_ids.man_last_purchase_date
            )
            last_purchase_date = template.product_variant_ids.last_purchase_date
            man_last_purchase_date = template.man_last_purchase_date
            if man_last_purchase_date and man_last_purchase_date > last_purchase_date:
                last_purchase_date = man_last_purchase_date
            template.last_purchase_date = last_purchase_date
        for template in self - unique_variants:
            template.man_last_purchase_date = False
            template.last_purchase_date = False

    # This method is triggered upon save, therefore the UX of last_purchase_date update
    # of product.template is not as instant as that of product.product.
    def _inverse_man_last_purchase_date(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.man_last_purchase_date = (
                    template.man_last_purchase_date
                )
