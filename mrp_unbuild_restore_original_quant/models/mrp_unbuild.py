# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    def _prepare_move_line_vals(self, move, origin_move_line, taken_quantity):
        vals = super()._prepare_move_line_vals(move, origin_move_line, taken_quantity)
        if origin_move_line.owner_id:
            vals["owner_id"] = origin_move_line.owner_id.id
        return vals

    def action_unbuild(self):
        self.ensure_one()
        if self.mo_id:
            self = self.with_context(exact_unbuild=True)
        return super().action_unbuild()

    def _generate_produce_moves(self):
        if not self.env.context.get("exact_unbuild"):
            return super()._generate_produce_moves()
        # i.e. There is production order for the unbuild
        moves = self.env["stock.move"]
        for unbuild in self:
            raw_moves = unbuild.mo_id.move_raw_ids.filtered(
                lambda move: move.state == "done"
            )
            factor = (
                unbuild.product_qty
                / unbuild.mo_id.product_uom_id._compute_quantity(
                    unbuild.mo_id.product_qty, unbuild.product_uom_id
                )
            )
            for raw_move in raw_moves:
                move = unbuild._generate_move_from_existing_move(
                    raw_move,
                    factor,
                    raw_move.location_dest_id,
                    self.location_dest_id,
                )
                if move.has_tracking == "none":
                    for move_line in raw_move.move_line_ids:
                        self.env["stock.move.line"].create(
                            {
                                "move_id": move.id,
                                "owner_id": move_line.owner_id.id,
                                "qty_done": move_line.qty_done,
                                "product_id": move.product_id.id,
                                "product_uom_id": move.product_uom.id,
                                "location_id": move.location_id.id,
                                "location_dest_id": move.location_dest_id.id,
                            }
                        )
                    move.write({"state": "confirmed"})
                moves += move
        return moves
