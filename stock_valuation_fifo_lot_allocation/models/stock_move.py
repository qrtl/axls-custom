# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_fifo_candidate_lines(self):
        self.ensure_one()
        return self.env["stock.move.line"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("company_id", "=", self.company_id.id),
                ("qty_remaining", ">", 0),
            ]
        )

    def _create_out_lot_allocations(self, layer, consumed_before):
        self.ensure_one()
        if not layer or not layer._is_lot_allocation_applicable():
            return
        amounts = defaultdict(float)
        quantities = defaultdict(float)
        for ml, (qty_before, value_before) in consumed_before.items():
            if ml.qty_consumed != qty_before:
                quantities[ml.lot_id] -= ml.qty_consumed - qty_before
            if ml.value_consumed != value_before:
                amounts[ml.lot_id] -= ml.value_consumed - value_before
        layer._create_lot_allocations(
            amounts_by_lot=amounts, quantities_by_lot=quantities
        )

    def _create_in_svl(self, forced_quantity=None):
        layers = super()._create_in_svl(forced_quantity=forced_quantity)
        layers._create_lot_allocations()
        return layers

    def _create_out_svl(self, forced_quantity=None):
        layers = self.env["stock.valuation.layer"]
        for move in self:
            candidates = move._get_fifo_candidate_lines()
            consumed_before = {
                ml: (ml.qty_consumed, ml.value_consumed) for ml in candidates
            }
            layer = super(StockMove, move)._create_out_svl(
                forced_quantity=forced_quantity
            )
            layers |= layer
            move._create_out_lot_allocations(layer, consumed_before)
        return layers
