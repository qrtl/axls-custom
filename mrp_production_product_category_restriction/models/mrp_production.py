# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_confirm(self):
        for production in self:
            if production.subcontractor_id:
                continue
            product = production.product_id
            if not product.categ_id.produce_ok:
                raise UserError(
                    _(
                        "%s is not allowed to be produced according to "
                        "the product category setting.",
                        product.name,
                    )
                )
        return super().action_confirm()
