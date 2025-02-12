# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Stockpick(models.Model):
    _inherit = 'stock.picking'

    allow_price_inconsistency = fields.Boolean(
        copy=False,
        help="If enabled, no error is raised for price inconsistency between "
        "recieved price and valuation price",
    )

    def _action_done(self):
        for pick in self:
            if pick.picking_type_id.code != 'incoming':
                continue
            if pick.allow_price_inconsistency:
                continue            
            for move in pick.move_ids_without_package:
                product = move.product_id
                threshold_type = product.price_discrepancy_threshold_type or pick.company_id.price_discrepancy_threshold_type
                if not threshold_type or threshold_type == "ignore":
                    continue
                threshold_value = product.price_discrepancy_threshold_value or pick.company_id.price_discrepancy_threshold_value
                if threshold_value <= 0.0:
                    continue
                received_price = move.price_unit
                inventory_price = product.standard_price
                price_difference = abs(received_price - inventory_price)
                if threshold_type == 'percentage':
                    percentage_difference = (price_difference / inventory_price) * 100 if inventory_price else 0
                    if percentage_difference > threshold_value:
                        self._log_price_discrepancy(product, received_price, inventory_price)
                else:
                    if price_difference > threshold_value:
                        self._log_price_discrepancy(product, received_price, inventory_price)
        return super()._action_done()

    def _log_price_discrepancy(self, product, received_price, inventory_price):
        message = _(f"Price discrepancy detected for {product.name}: Received Price = {received_price}, Inventory Price = {inventory_price}.")
        self.message_post(body=message)
        raise UserError(message)
