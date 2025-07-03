# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("categ_id", "tracking")
    def _check_specific_identification_tracking(self):
        for rec in self:
            if (
                rec.categ_id.enable_specific_identification_method
                and rec.categ_id.property_cost_method == "fifo"
                and rec.tracking == "none"
            ):
                raise ValidationError(
                    _(
                        "The selected category requires this product to use "
                        "serial or lot tracking."
                    )
                )
