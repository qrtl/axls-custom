# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    account_line_ids = fields.One2many("analytic.account.line", "account_id")
    related_account_ids = fields.Many2many(
        "account.analytic.account",
        string="Related accounts (all plans)",
        compute="_compute_related_accounts",
    )

    @api.depends("account_line_ids.account_ids")
    def _compute_related_accounts(self):
        for rec in self:
            rec.related_account_ids = rec.account_line_ids.mapped("account_ids")
