# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAnalylticPlan(models.Model):
    _inherit = "account.analytic.plan"

    plan_type = fields.Selection(
        selection=[
            ("project", "Project"),
            ("department", "Department"),
        ],
        help="This selection will affect which column the analytic account will be "
        "mapped to in the OBC data export.",
    )
