# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        if (
            self.env.user.has_group("product_security.group_product_manager")
            or self.env.user.id == SUPERUSER_ID
        ):
            return super().write(vals)
        if "categ_id" in vals:
            raise UserError(
                _(
                    "You are not allowed to update product category. Please contact "
                    "the administrator as necessary."
                )
            )
        return super().write(vals)
