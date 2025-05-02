# Copyright 2025 Quartile Limited (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class AnalyticMixin(models.AbstractModel):
    _inherit = "analytic.mixin"

    @api.model
    def _format_distribution(self, dist):
        result = []
        # Normally, when all analytic lines are removed, the value of
        # analytic_distribution becomes an empty dictionary ({}).
        # However, on the inventory adjustment page, if the analytic
        # field is cleared, the analytic_distribution in the vals passed
        # to write() becomes False.
        # Therefore, this conditional check is added to handle that case.
        if not dist:
            return result
        for account_id, percent in dist.items():
            account = self.env["account.analytic.account"].browse(int(account_id))
            plan_name = account.plan_id.name
            result.append(f"{plan_name}: {account.name} {percent}%")
        return result
