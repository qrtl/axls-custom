# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    scheduled_date = fields.Date(
        compute="_compute_scheduled_date",
        inverse="_inverse_set_scheduled_date",
        store=True,
        index=True,
        default=fields.Date.today,
        tracking=True,
        states={"done": [("readonly", True)], "cancel": [("readonly", True)]},
        help="Scheduled time for the first part of the shipment to be processed."
        "Setting manually a value here would set it as expected date for all the stock moves.",
    )
