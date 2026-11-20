# Copyright 2026 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    is_direct_ship = fields.Boolean(
        string="Direct Ship",
        help="When enabled, incoming transfers for this analytic account are "
        "automatically rerouted to the immediate shipment location.",
    )
