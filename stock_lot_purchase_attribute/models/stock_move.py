# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        receipt_moves = moves.filtered(lambda x: x.purchase_line_id)
        for line in receipt_moves.move_line_ids:
            if not line.lot_id:
                continue
            purchase_line = line.move_id.purchase_line_id
            line.lot_id.write(
                {
                    "purchase_id": purchase_line.order_id.id,
                    "purchase_partner_id": purchase_line.partner_id,
                }
            )
        return moves
