# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class AnalyticMixin(models.AbstractModel):
    _inherit = "analytic.mixin"

    def _format_distribution(self, dist):
        result = []
        for account_id, percent in dist.items():
            account = self.env["account.analytic.account"].browse(int(account_id))
            if account.exists():
                plan_name = account.plan_id.name or ""
                result.append(f"{plan_name}:{account.name}:{float(percent)}%")
        return result
