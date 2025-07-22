# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AnalyticAccountLine(models.Model):
    _name = "analytic.account.line"

    account_id = fields.Many2one("account.analytic.account", ondelete="cascade")
    plan_id = fields.Many2one("account.analytic.plan", required=True)
    account_ids = fields.Many2many(
        "account.analytic.account", string="Related Accounts", required=True
    )
