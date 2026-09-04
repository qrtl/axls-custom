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

    @api.model
    def _get_budget_account_ids(self, distributions):
        """Return the accounts of a budget plan the given distributions hold.

        Every account of a budget plan counts here, without regard for the
        company: whether or not it resolves to the budget number of a line, it
        is not the business of the purchase order header. Archived accounts
        count as well, and the accounts are searched rather than browsed, as
        the json field holds no database reference and may still refer to a
        deleted account. Takes the distributions of a whole order at once, as
        the callers run over every line of one.
        """
        account_ids = set()
        for distribution in distributions:
            account_ids.update(int(account_id) for account_id in distribution or {})
        if not account_ids:
            return set()
        return set(
            self.env["account.analytic.account"]
            .with_context(active_test=False)
            .search(
                [
                    ("id", "in", list(account_ids)),
                    ("is_budget_account", "=", True),
                ]
            )
            .ids
        )

    @api.model
    def _split_distribution_by_budget(self, distribution, budget_account_ids):
        """Split a distribution into its budget number part and the rest.

        The two parts are distributions of their own: a plan takes 100% of the
        distribution on its own, so dropping the accounts of one plan leaves
        the others whole.
        """
        budget, other = {}, {}
        for account_id, percentage in (distribution or {}).items():
            part = budget if int(account_id) in budget_account_ids else other
            part[account_id] = percentage
        return budget, other

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
