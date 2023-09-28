# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        if "categ_id" in vals:
            if not self.env.user.has_group("product_security.group_product_manager"):
                raise UserError(
                    _(
                        "You are not allowed to update product category."
                        " Please contact administrator as necessary."
                    )
                )
        return super(ProductTemplate, self).write(vals)
