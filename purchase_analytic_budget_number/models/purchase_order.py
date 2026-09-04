# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_line_distributions(self):
        """Return the distribution of each line as it stands, keyed by line.

        Taken before purchase_analytic applies the distribution of the header,
        as that replaces the distribution of a line whole, its budget number
        included, which leaves this as the only place the budget number is
        still to be found. Nothing is looked up here on purpose: a search
        flushes the environment, and the recompute that comes with it would
        take the value the header is being given away from under it before
        super() gets to read it.
        """
        self.ensure_one()
        return {
            line: dict(line.analytic_distribution or {}) for line in self.order_line
        }

    def _restore_line_budget_numbers(self, distributions):
        """Put the budget numbers of the given distributions back on the lines.

        The budget number of a line is none of the header's business, so it is
        carried over the write purchase_analytic makes rather than lost to it.
        """
        self.ensure_one()
        line_model = self.env["purchase.order.line"]
        budget_account_ids = line_model._get_budget_account_ids(distributions.values())
        for line, distribution in distributions.items():
            budget = line_model._split_distribution_by_budget(
                distribution, budget_account_ids
            )[0]
            if budget:
                line.analytic_distribution = {
                    **(line.analytic_distribution or {}),
                    **budget,
                }

    @api.depends("order_line.analytic_distribution")
    def _compute_analytic_distribution(self):
        """Leave the budget numbers of the lines out of the header.

        purchase_analytic compares the distributions of the lines whole, so
        lines that agree on everything but their budget number leave the header
        empty, and the budget number of an order with a single line ends up on
        the header. The orders with lines are settled here instead, on the same
        comparison with the budget numbers left out, which also keeps a budget
        number from ever reaching the header. super() is what still settles the
        orders without lines, which keep the value the user gave them.
        """
        res = super()._compute_analytic_distribution()
        line_model = self.env["purchase.order.line"]
        budget_account_ids = line_model._get_budget_account_ids(
            self.order_line.mapped("analytic_distribution")
        )
        for po in self.filtered("order_line"):
            distributions = [
                line_model._split_distribution_by_budget(
                    line.analytic_distribution, budget_account_ids
                )[1]
                for line in po.order_line
            ]
            common = distributions[0]
            if any(distribution != common for distribution in distributions[1:]):
                common = {}
            po.analytic_distribution = common or False
        return res

    def _inverse_analytic_distribution(self):
        """Keep the budget numbers of the lines through the write of the header."""
        distributions = {po: po._get_line_distributions() for po in self}
        res = super()._inverse_analytic_distribution()
        for po in self:
            po._restore_line_budget_numbers(distributions[po])
        return res

    @api.onchange("analytic_distribution")
    def _onchange_analytic_distribution(self):
        """Same as the inverse, on a form whose lines are not stored yet."""
        distributions = self._get_line_distributions()
        res = super()._onchange_analytic_distribution()
        self._restore_line_budget_numbers(distributions)
        return res
