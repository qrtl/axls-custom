# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    enable_acceptance_tester_check = fields.Boolean(
        "Acceptance Tester Check",
        related="company_id.enable_acceptance_tester_check",
        readonly=False,
        help="Enable the check on the Acceptance Tester field in purchase orders "
        "to determine whether setting a value is required or not.",
    )
