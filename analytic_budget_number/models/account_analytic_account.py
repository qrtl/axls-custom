# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    subsystem = fields.Char(
        help="Subsystem the budget number relates to. Available in the analytic "
        "account search view as a filter and as a group-by.",
    )
    component = fields.Char(
        help="Component the budget number relates to. Available in the analytic "
        "account search view as a filter and as a group-by.",
    )
    model_type = fields.Selection(
        [("EM", "EM"), ("FM", "FM"), ("Racksat", "Racksat")],
        string="Model",
        help="Model the budget number relates to. Available in the analytic "
        "account search view as a filter and as a group-by.",
    )
    description = fields.Char(
        help="What the budget number is for, in free text. Available as a "
        "column of the analytic account list.",
    )
    is_budget_account = fields.Boolean(
        related="root_plan_id.is_budget",
        string="Is Budget Account",
        help="Technical field: this account belongs to the plan holding the "
        "budget numbers, or to one of its subplans, so it stands for a budget "
        "number itself. Drives the visibility of the attributes above.",
    )
