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

                if old_dist == new_dist:
                    continue

                old_lines = record._format_distribution(old_dist)
                new_lines = record._format_distribution(new_dist)

                old_formatted = "<br/>".join(old_lines)
                new_formatted = "<br/>".join(new_lines)

                record.message_post(
                    body=_(
                        "Analytic Distribution updated<br/><br/>"
                        "From:<br/> %(from)s<br/><br/>"
                        "To:<br/> %(to)s"
                    )
                    % {
                        "from": old_formatted,
                        "to": new_formatted,
                    }
                )

        return super(StockLot, self).write(vals)
