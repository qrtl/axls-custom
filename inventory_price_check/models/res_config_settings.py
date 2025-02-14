# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    price_discrepancy_threshold_type = fields.Selection(
        related="company_id.price_discrepancy_threshold_type", readonly=False
    )
    price_discrepancy_threshold_value = fields.Float(
        related="company_id.price_discrepancy_threshold_value",
        readonly=False,
        string="Global Threshold Value",
        help="Global threshold value for price discrepancy warnings.",
    )
