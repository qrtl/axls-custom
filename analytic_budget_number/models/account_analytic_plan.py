# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAnalyticPlan(models.Model):
    _inherit = "account.analytic.plan"

    is_budget = fields.Boolean(
        string="Use for Purchase Order Lines Budget",
        help="The account of this plan is shown as the budget number of the "
        "purchase order lines it is distributed to.",
    )

    def _get_conflicting_budget_plan(self):
        """Return a flagged plan whose company overlaps with the one of this plan.

        A plan without company applies to every company, so it conflicts with
        any other flagged plan. sudo, as the multi company record rule would
        otherwise hide a conflicting plan from a user who has not activated its
        company, and let a second budget plan through.
        """
        self.ensure_one()
        domain = [("is_budget", "=", True), ("id", "!=", self.id)]
        if self.company_id:
            domain.append(("company_id", "in", [False, self.company_id.id]))
        return self.sudo().search(domain, limit=1)

    @api.constrains("is_budget", "company_id")
    def _check_unique_budget_plan(self):
        for plan in self:
            if not plan.is_budget:
                continue
            existing = plan._get_conflicting_budget_plan()
            if existing:
                raise ValidationError(
                    _(
                        "Only one analytic plan can be set for the purchase order "
                        "lines of a company. Please disable the existing plan "
                        "'%(plan)s' first.",
                        plan=existing.display_name,
                    )
                )
