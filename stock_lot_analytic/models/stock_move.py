# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if (
                move.location_id.usage == "internal"
                or move.location_dest_id.usage != "internal"
                or not move.lot_ids
                or not move.analytic_distribution
            ):
                continue
            move.lot_ids.write({"analytic_distribution": move.analytic_distribution})
        return res
