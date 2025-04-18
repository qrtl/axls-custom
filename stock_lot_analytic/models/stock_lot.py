# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class StockLot(models.Model):
    _name = "stock.lot"
    _inherit = ["stock.lot", "analytic.mixin"]

    def write(self, vals):
        for record in self:
            if "analytic_distribution" in vals:
                old_dist = record.analytic_distribution or {}
                new_dist = vals.get("analytic_distribution") or {}

                def _format_distribution(dist):
                    result = []
                    for account_id, percent in dist.items():
                        account = self.env["account.analytic.account"].browse(
                            int(account_id)
                        )
                        if account.exists():
                            plan_name = account.plan_id.name or ""
                            result.append(
                                f"{plan_name}:{account.name}:{float(percent)}%"
                            )
                    return ",<br/>".join(result)

                old_formatted = _format_distribution(old_dist)
                new_formatted = _format_distribution(new_dist)

                if old_formatted != new_formatted:
                    record.message_post(
                        body=_(
                            "Analytic Distribution updated<br/><br/>"
                            "Before:<br/> %(before)s<br/><br/>"
                            "After:<br/> %(after)s"
                        )
                        % {
                            "before": old_formatted,
                            "after": new_formatted,
                        }
                    )

        return super(StockLot, self).write(vals)
