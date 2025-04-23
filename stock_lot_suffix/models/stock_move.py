# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if not move.lot_ids:
                continue
            purchase_line = move.purchase_line_id
            move.lot_ids.write(
                {"channel_category": purchase_line.order_id.channel_category}
            )
        return res
