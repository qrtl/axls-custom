# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_acceptance_tester = fields.Boolean(
        "Acceptance Tester",
        help="Select this field if the partner is an acceptance tester.",
    )
