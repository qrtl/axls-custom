# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class StockLot(models.Model):
    _name = "stock.lot"
    _inherit = ["stock.lot", "analytic.mixin"]

    def write(self, vals):
        if "analytic_distribution" not in vals:
            return super().write(vals)
        for record in self:
            new_dist = vals.get("analytic_distribution") or {}
            old_dist = record.analytic_distribution or {}
            if old_dist == new_dist:
                continue
            new_lines = record._format_distribution(new_dist)
            old_lines = record._format_distribution(old_dist)
            new_formatted = "<br/>".join(new_lines)
            old_formatted = "<br/>".join(old_lines)
            record.message_post(
                body=_(
                    "Analytic Distribution updated<br/><br/>"
                    "To:<br/> %(to)s<br/><br/>"
                    "From:<br/> %(from)s"
                )
                % {
                    "to": new_formatted,
                    "from": old_formatted,
                }
            )
        return super(StockLot, self).write(vals)
