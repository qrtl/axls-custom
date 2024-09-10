# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    # We make these field editable on purpose so that the user can change the price as
    # appropriate.
    purchase_id = fields.Many2one(
        "purchase.order",
        "Purchase Order",
        tracking=True,
    )
    purchase_partner_id = fields.Many2one(
        "res.partner",
        "Vendor",
        tracking=True,
    )
