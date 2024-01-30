# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import float_round


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    def action_unbuild(self):
        self.ensure_one()
        self = self.with_context(exact_unbuild=True)
        return super(MrpUnbuild, self).action_unbuild()

    def _generate_produce_moves(self):
        if self.env.context.get('exact_unbuild'):
            moves = self.env['stock.move']
            for unbuild in self:
                if unbuild.mo_id:
                    raw_moves = unbuild.mo_id.move_raw_ids.filtered(lambda move: move.state == 'done')
                    factor = unbuild.product_qty / unbuild.mo_id.product_uom_id._compute_quantity(unbuild.mo_id.product_qty, unbuild.product_uom_id)
                    for raw_move in raw_moves:
                        move = unbuild._generate_move_from_existing_move(raw_move, factor, raw_move.location_dest_id, self.location_dest_id)
                        if move.has_tracking == 'none':
                            for move_line in raw_move.move_line_ids:
                                self.env['stock.move.line'].create({
                                    'move_id': move.id,
                                    'owner_id': move_line.owner_id.id,
                                    'qty_done': move_line.qty_done,
                                    'product_id': move.product_id.id,
                                    'product_uom_id': move.product_uom.id,
                                    'location_id': move.location_id.id,
                                    'location_dest_id': move.location_dest_id.id,
                                })
                            move.write({'state': 'confirmed'})
                        moves += move
                else:
                    factor = unbuild.product_uom_id._compute_quantity(unbuild.product_qty, unbuild.bom_id.product_uom_id) / unbuild.bom_id.product_qty
                    boms, lines = unbuild.bom_id.explode(unbuild.product_id, factor, picking_type=unbuild.bom_id.picking_type_id)
                    for line, line_data in lines:
                        move = unbuild._generate_move_from_bom_line(line.product_id, line.product_uom_id, line_data['qty'], bom_line_id=line.id)
                        self.env['stock.move.line'].create({
                            'move_id': move.id,
                            'qty_done': move.quantity_done,
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                        })
                        move.write({'state': 'confirmed'})
                        moves += move
            return moves
        return super(MrpUnbuild, self)._generate_produce_moves()
