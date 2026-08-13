# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    analytic_budget_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Budget",
        compute="_compute_analytic_budget_id",
        store=True,
    )

    def _get_distribution_account_ids(self):
        """Return the analytic account ids the keys of the distribution hold."""
        self.ensure_one()
        return [int(account_id) for account_id in self.analytic_distribution or {}]

    def _get_budget_plan(self, budget_plans):
        """Return the budget plan that applies to the company of the line.

        A plan without company applies to every company. At most one plan can
        apply, as _check_unique_budget_plan rejects overlapping ones.
        """
        self.ensure_one()
        return budget_plans.filtered(
            lambda plan: not plan.company_id or plan.company_id == self.company_id
        )[:1]

    def _get_budget_accounts(self, budget_accounts):
        """Return the accounts of the budget plan that apply to the line.

        An account without company applies to every company. The accounts of a
        budget plan shared by every company may belong to any of them, so only
        those of the company of the line are budget numbers for it.
        """
        self.ensure_one()
        return budget_accounts.filtered(
            lambda account: not account.company_id
            or account.company_id == self.company_id
        )

    @api.depends("analytic_distribution", "company_id")
    def _compute_analytic_budget_id(self):
        # The compute runs as superuser, as compute_sudo defaults to store, so
        # the plans of every company are found here. The one that applies is
        # then taken per line from the company of the line.
        budget_plans = self.env["account.analytic.plan"].search(
            [("is_budget", "=", True)]
        )
        if not budget_plans:
            self.analytic_budget_id = False
            return
        account_ids = set()
        for line in self:
            account_ids.update(line._get_distribution_account_ids())
        # Search instead of browse, as the json field holds no database
        # reference and may still refer to a deleted account. Archived accounts
        # count, as the budget number of the lines they were distributed to
        # should not be lost. child_of, as the accounts of a budget plan may sit
        # on its subplans, which is how the distribution resolves them too.
        accounts_by_plan_id = {
            plan.id: self.env["account.analytic.account"]
            .with_context(active_test=False)
            .search(
                [
                    ("id", "in", list(account_ids)),
                    ("plan_id", "child_of", plan.id),
                ]
            )
            for plan in budget_plans
        }
        no_account = self.env["account.analytic.account"]
        for line in self:
            budget_accounts = accounts_by_plan_id.get(
                line._get_budget_plan(budget_plans).id, no_account
            )
            budget_account_ids = set(line._get_budget_accounts(budget_accounts).ids)
            # The distribution holds the accounts of the budget plan in no
            # meaningful order, as jsonb does not keep the order the keys were
            # written in. Take the oldest one, so that the budget number does
            # not depend on the moment the line is computed at.
            line.analytic_budget_id = min(
                budget_account_ids.intersection(line._get_distribution_account_ids()),
                default=False,
            )
