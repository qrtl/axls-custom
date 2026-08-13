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

    def unlink(self):
        # analytic_distribution holds no database reference to the accounts, so
        # nothing else would recompute the budget number of the lines a deleted
        # account was distributed to, and it would be lost instead of falling
        # back to the next budget account of the distribution. Collect the lines
        # before the delete, as the distribution is what they are found by, and
        # in sudo, as the deletion is no reason to need access to them.
        lines = (
            self.env["purchase.order.line"]
            .sudo()
            .search([("analytic_distribution", "in", self.ids)])
        )
        res = super().unlink()
        lines.modified(["analytic_distribution"])
        return res
