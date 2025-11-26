# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools import float_round


class UOM(models.Model):
    _inherit = "uom.uom"

    def _compute_price(self, price, to_unit):
        self.ensure_one()
        aml = self.env.context.get("need_deposit_adj_aml")
        if aml and aml.quantity:
            price = float_round(
                aml.balance / aml.quantity,
                precision_rounding=aml.company_currency_id.rounding,
            )
        return super()._compute_price(price, to_unit)
