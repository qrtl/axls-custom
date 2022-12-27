# Copyright 2022 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "analytic.mixin"]

    @api.onchange("analytic_distribution")
    def onchange_analytic_distribution(self):
        moves = self.move_ids.filtered(lambda x: not x.analytic_distribution)
        moves.write({"analytic_distribution": self.analytic_distribution})
        move_lines = self.move_line_ids.filtered(lambda x: not x.analytic_distribution)
        move_lines.write({"analytic_distribution": self.analytic_distribution})
