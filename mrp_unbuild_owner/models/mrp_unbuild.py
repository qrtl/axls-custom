# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    def action_validate(self):
        owner = self.mo_id.owner_id
        if owner:
            self = self.with_context(force_restricted_owner_id=owner)
        return super().action_validate()

    def _prepare_move_line_vals(self, move, origin_move_line, taken_quantity):
        vals = super()._prepare_move_line_vals(move, origin_move_line, taken_quantity)
        vals["owner_id"] = origin_move_line.owner_id.id
        return vals

    def action_unbuild(self):
        self.ensure_one()
        if self.mo_id:
            self = self.with_context(exact_unbuild=True)
        return super().action_unbuild()

    def _get_move_line_vals(self, move, move_line):
        return {
            "move_id": move.id,
            "owner_id": move_line.owner_id.id,
            "qty_done": min(move.product_uom_qty, move_line.qty_done),
            "product_id": move.product_id.id,
            "product_uom_id": move.product_uom.id,
            "location_id": move.location_id.id,
            "location_dest_id": move.location_dest_id.id,
        }

    def _generate_produce_moves(self):
        """This logic is a bit hard to understand but necessary due to how the following
        steps are written in the standard code:
        https://github.com/OCA/OCB/blob/52bec03/addons/mrp/models/mrp_unbuild.py#L189-L207
        In short, we want to prepare stock.move.line records in advance with the
        "correct" content before the standard code generates them with incorrectly
        (without owner).
        """
        if not self.env.context.get("exact_unbuild"):
            return super()._generate_produce_moves()
        # i.e. There is production order for the unbuild
        # We need to remove the force_restrict_owner_id assignment to respect the owner
        # of the original move line.
        self = self.with_context(default_lot_id=False, force_restricted_owner_id=False)
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
                    vals_list = []
                    for move_line in raw_move.move_line_ids:
                        vals = self._get_move_line_vals(move, move_line)
                        vals_list.append(vals)
                    self.env["stock.move.line"].create(vals_list)
                    move.write({"state": "confirmed"})
                moves += move
        return moves.with_context(produce_moves=True)
