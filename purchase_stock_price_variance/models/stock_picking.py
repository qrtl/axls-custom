# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class Stockpick(models.Model):
    _inherit = "stock.picking"

    bypass_price_variance_check = fields.Boolean(
        copy=False,
        tracking=True,
        help="If enabled, no error is raised for price variance between "
        "the product's standard price and purchase receipt unit price.",
    )

    def write(self, vals):
        if "bypass_price_variance_check" in vals:
            if not self.env.user.has_group(
                "purchase_stock_price_variance.group_bypass_price_variance_check"
            ):
                raise UserError(
                    _(
                        "You do not have permission to modify the "
                        "'Bypass Price Variance Check' field. "
                        "Please contact an administrator or a user "
                        "with the appropriate permissions."
                    )
                )
        return super().write(vals)

    def _action_done(self):
        if not self.env.company.price_variance_threshold:
            return super()._action_done()
        global_price_variance_threshold_percent = (
            self.env.company.price_variance_threshold_percent
        )
        global_price_variance_threshold_amount = (
            self.env.company.price_variance_threshold_amount
        )
        for pick in self:
            if pick.bypass_price_variance_check:
                continue
            for move in pick.move_ids:
                if not (move._is_in() or move._is_dropshipped()):
                    continue
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
                received_price = move._get_price_unit()
                standard_price = product.standard_price
                amount_difference = abs(received_price - standard_price)
                percentage_difference = (
                    (amount_difference / standard_price) * 100 if standard_price else 0
                )
                if (
                    threshold_percent and percentage_difference > threshold_percent
                ) or (threshold_amount and amount_difference > threshold_amount):
                    raise UserError(
                        _(
                            f"Price variance exceeding a threshold detected for "
                            f"{product.name}: Received Price = {received_price}, "
                            f"Proudct Price = {standard_price}."
                        )
                    )
        return super()._action_done()
