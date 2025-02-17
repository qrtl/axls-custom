# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class Stockpick(models.Model):
    _inherit = "stock.picking"

    bypass_price_variance_check = fields.Boolean(
        copy=False,
        tracking=True,
        groups="purchase_stock_price_variance.group_bypass_price_variance_check",
        help="If enabled, no error is raised for price variance between "
        "the product's standard price and purchase receipt unit price.",
    )

    def _action_done(self):
        global_price_variance_threshold_percent = (
            self.env.company.price_variance_threshold_percent
        )
        global_price_variance_threshold_amount = (
            self.env.company.price_variance_threshold_amount
        )
        for pick in self:
            if pick.picking_type_id.code != "incoming":
                continue
            if pick.sudo().bypass_price_variance_check:
                continue
            for move in pick.move_ids_without_package:
                product = move.product_id
                if product.bypass_price_variance_check:
                    continue
                threshold_percent = (
                    product.price_variance_threshold_percent
                    or global_price_variance_threshold_percent
                )
                threshold_amount = (
                    product.price_variance_threshold_amount
                    or global_price_variance_threshold_amount
                )
                received_price = move.price_unit
                standard_price = product.standard_price
                amount_difference = abs(received_price - standard_price)
                percentage_difference = (
                    (amount_difference / standard_price) * 100 if standard_price else 0
                )
                if (
                    percentage_difference > threshold_percent
                    or amount_difference > threshold_amount
                ):
                    raise UserError(
                        _(
                            f"Price discrepancy detected for {product.name}: "
                            f"Received Price = {received_price}, Proudct Price"
                            f" = {standard_price}."
                        )
                    )
        return super()._action_done()
