# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _is_fifo_lot_move(self):
        self.ensure_one()
        product = self.product_id.with_company(self.company_id)
        return product.cost_method == "fifo" and product.tracking != "none"

    def _create_in_svl(self, forced_quantity=None):
        layers = super()._create_in_svl(forced_quantity=forced_quantity)
        if not forced_quantity:
            # stock_valuation_fifo_lot sets qty_base in the move UoM here and
            # converts it to the product UoM only at the end of _action_done().
            for ml in layers.stock_move_id.filtered(
                lambda x: x._is_fifo_lot_move()
            ).move_line_ids:
                ml.qty_base = ml.product_uom_id._compute_quantity(
                    ml.qty_done, ml.product_id.uom_id
                )
        layers._allocate_to_lots()
        return layers

    def _create_out_svl(self, forced_quantity=None):
        layers = self.env["stock.valuation.layer"]
        for move in self:
            candidates = self.env["stock.move.line"]
            if move._is_fifo_lot_move():
                candidates = candidates.search(
                    [
                        ("product_id", "=", move.product_id.id),
                        ("company_id", "=", move.company_id.id),
                        ("qty_remaining", ">", 0),
                    ]
                )
            consumed_before = {
                ml: (ml.qty_consumed, ml.value_consumed) for ml in candidates
            }
            layer = super(StockMove, move)._create_out_svl(
                forced_quantity=forced_quantity
            )
            layers |= layer
            if not layer or not layer._is_lot_allocation_applicable():
                continue
            # Charge each lot what the FIFO run consumed from it.
            amounts = defaultdict(float)
            quantities = defaultdict(float)
            for ml, (qty_before, value_before) in consumed_before.items():
                amounts[ml.lot_id] -= ml.value_consumed - value_before
                quantities[ml.lot_id] -= ml.qty_consumed - qty_before
            self.env["stock.valuation.lot.allocation"].sudo().create(
                layer._prepare_lot_allocation_vals(amounts, quantities)
            )
        return layers
