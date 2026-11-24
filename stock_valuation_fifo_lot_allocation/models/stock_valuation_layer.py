# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.tools import float_is_zero, float_round

_logger = logging.getLogger(__name__)

# Layers with a lower id are still to be backfilled.
BACKFILL_PARAM = "stock_valuation_fifo_lot_allocation.backfill_before_id"
BACKFILL_DONE = -1


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    lot_allocation_ids = fields.One2many(
        "stock.valuation.lot.allocation",
        "valuation_layer_id",
        string="Lot Allocations",
    )

    @api.model_create_multi
    def create(self, vals_list):
        layers = super().create(vals_list)
        # Quantity-bearing layers are allocated from stock.move.
        layers.filtered(lambda x: not x.quantity)._allocate_to_lots()
        return layers

    def _is_lot_allocation_applicable(self):
        self.ensure_one()
        product = self.product_id.with_company(self.company_id)
        return (
            product.cost_method == "fifo"
            and product.tracking != "none"
            and (self.quantity or not self.currency_id.is_zero(self.value))
        )

    def _get_lot_out_quantities(self):
        """Return the quantity per lot that the outgoing layers took, in the product
        UoM, charged to the lot whose FIFO balance was consumed.
        """
        quantities = defaultdict(float)
        for layer in self:
            for ml in layer.stock_move_id.move_line_ids.filtered("lot_id"):
                lot = ml.force_fifo_lot_id or ml.lot_id
                quantities[lot] += ml.product_uom_id._compute_quantity(
                    ml.qty_done, layer.product_id.uom_id
                )
        return quantities

    def _get_lot_receipt_lines(self, lots):
        """Return the incoming move lines per lot of the layer's product."""
        self.ensure_one()
        lines = self.env["stock.move.line"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("company_id", "=", self.company_id.id),
                ("lot_id", "in", lots.ids),
                ("qty_base", ">", 0),
            ]
        )
        lines_by_lot = defaultdict(lambda: self.env["stock.move.line"])
        for ml in lines:
            lines_by_lot[ml.lot_id] |= ml
        return lines_by_lot

    def _get_lot_remaining_qty_at_layer(self):
        """Return the remaining quantity per lot when the layer was posted.

        That is the current one plus what later outgoing layers took, which is
        exact for a lot received once. A lot received several times keeps its
        current quantity, as which receipt the later layers drew on is not known.
        """
        self.ensure_one()
        move = self.stock_move_id or self.stock_valuation_layer_id.stock_move_id
        if move:
            lines = move.move_line_ids.filtered(lambda x: x.lot_id and x.qty_base > 0)
        else:
            lines = self.env["stock.move.line"].search(
                [
                    ("product_id", "=", self.product_id.id),
                    ("company_id", "=", self.company_id.id),
                    ("lot_id", "!=", False),
                    ("qty_base", ">", 0),
                    ("move_id.stock_valuation_layer_ids.id", "<", self.id),
                ]
            )
        receipt_lines = self._get_lot_receipt_lines(lines.lot_id)
        later_out = self.search(
            [
                ("product_id", "=", self.product_id.id),
                ("company_id", "=", self.company_id.id),
                ("quantity", "<", 0),
                ("id", ">", self.id),
            ]
        )._get_lot_out_quantities()
        quantities = defaultdict(float)
        for ml in lines:
            qty = ml.qty_remaining
            if len(receipt_lines[ml.lot_id]) == 1:
                qty = min(ml.qty_base, qty + later_out[ml.lot_id])
            quantities[ml.lot_id] += qty
        return quantities

    def _get_lot_out_amounts(self, quantities):
        """Return the amount per lot of an outgoing layer, without the FIFO run to
        read it from (backfill only).

        A lot received once was consumed at the rate of its receipt line, exact
        unless value landed on the receipt between its deliveries. The rest of the
        layer value goes to the other lots, prorated on their quantity.
        """
        self.ensure_one()
        receipt_lines = self._get_lot_receipt_lines(
            self.env["stock.lot"].browse([lot.id for lot in quantities])
        )
        amounts = {}
        others = {}
        for lot, qty in quantities.items():
            line = receipt_lines[lot]
            if len(line) == 1 and line.qty_consumed:
                amounts[lot] = -qty * line.value_consumed / line.qty_consumed
            else:
                others[lot] = qty
        if not others:
            # Only off when value landed between deliveries: scale to the layer.
            return self._prorate_value(amounts)
        residual = self.value - sum(amounts.values())
        total = sum(others.values())
        amounts.update({lot: residual * qty / total for lot, qty in others.items()})
        return amounts

    def _prorate_value(self, weights):
        self.ensure_one()
        total = sum(weights.values())
        if not total:
            return {}
        return {lot: self.value * weight / total for lot, weight in weights.items()}

    def _get_lot_allocation_split(self):
        """Return the quantity and the amount per lot of the layer."""
        self.ensure_one()
        if self.quantity > 0:
            quantities = defaultdict(float)
            for ml in self.stock_move_id.move_line_ids.filtered("lot_id"):
                quantities[ml.lot_id] += ml.qty_base
            return quantities, self._prorate_value(quantities)
        if self.quantity < 0:
            quantities = {
                lot: qty for lot, qty in self._get_lot_out_quantities().items() if qty
            }
            return (
                {lot: -qty for lot, qty in quantities.items()},
                self._get_lot_out_amounts(quantities),
            )
        return {}, self._prorate_value(self._get_lot_remaining_qty_at_layer())

    def _prepare_lot_allocation_vals(self, amounts, quantities, **values):
        """Round the amounts so that they add up to the layer value, the remainder
        going to the largest share.
        """
        self.ensure_one()
        currency = self.currency_id
        rounding = self.product_id.uom_id.rounding
        amounts = {lot: currency.round(amount) for lot, amount in amounts.items()}
        remainder = currency.round(self.value - sum(amounts.values()))
        if amounts and not currency.is_zero(remainder):
            largest = max(amounts, key=lambda lot: (abs(amounts[lot]), -lot.id))
            amounts[largest] += remainder
        vals_list = []
        for lot in dict.fromkeys([*amounts, *quantities]):
            amount = amounts.get(lot, 0.0)
            quantity = float_round(
                quantities.get(lot, 0.0), precision_rounding=rounding
            )
            if currency.is_zero(amount) and float_is_zero(
                quantity, precision_rounding=rounding
            ):
                continue
            vals_list.append(
                {
                    "lot_id": lot.id,
                    "valuation_layer_id": self.id,
                    "allocated_amount": amount,
                    "allocated_quantity": quantity,
                    "description": self.description,
                    **values,
                }
            )
        return vals_list

    def _allocate_to_lots(self):
        """Split each layer across its lots. Layers already allocated are skipped,
        which makes the backfill safe to re-run.
        """
        vals_list = []
        for layer in self:
            if not layer._is_lot_allocation_applicable() or layer.lot_allocation_ids:
                continue
            quantities, amounts = layer._get_lot_allocation_split()
            if amounts:
                vals_list += layer._prepare_lot_allocation_vals(amounts, quantities)
        return self.env["stock.valuation.lot.allocation"].sudo().create(vals_list)

    @api.model
    def _balance_lot_allocations(self):
        """Charge each lot's residual gap to an opening adjustment row on its last
        incoming layer, so that the per-lot invariant holds exactly.
        """
        allocations = self.env["stock.valuation.lot.allocation"].sudo()
        vals_list = []
        for lot_id, gap in allocations._get_lot_gaps().items():
            layer = self.sudo().search(
                [("lot_ids", "in", lot_id), ("quantity", ">", 0)],
                order="id desc",
                limit=1,
            )
            if not layer:
                _logger.warning(
                    "No incoming valuation layer found for lot %s; its allocation "
                    "gap of %s is left unbalanced.",
                    lot_id,
                    gap,
                )
                continue
            # The adjustment is not part of the layer value, so it is not rounded
            # to it.
            gap = layer.currency_id.round(gap)
            if not layer.currency_id.is_zero(gap):
                vals_list.append(
                    {
                        "lot_id": lot_id,
                        "valuation_layer_id": layer.id,
                        "allocated_amount": gap,
                        "description": _("Opening allocation adjustment"),
                        "is_opening_adjustment": True,
                    }
                )
        allocations.create(vals_list)

    @api.model
    def _cron_backfill_lot_allocations(self, limit):
        """Allocate the layers that have no allocation yet, newest first, one batch
        per run so that a run stays within the cron time limit. Once the backlog is
        drained, balance the lots and idle until the progress is cleared.
        """
        params = self.env["ir.config_parameter"].sudo()
        before_id = int(params.get_param(BACKFILL_PARAM, 0))
        if before_id == BACKFILL_DONE:
            return
        if not before_id:
            before_id = self.search([], order="id desc", limit=1).id + 1
        layers = self.search([("id", "<", before_id)], order="id desc", limit=limit)
        layers._allocate_to_lots()
        if len(layers) == limit:
            params.set_param(BACKFILL_PARAM, layers[-1].id)
            self.env.ref(
                "stock_valuation_fifo_lot_allocation.ir_cron_lot_allocation_backfill"
            )._trigger()
        else:
            self._balance_lot_allocations()
            # A running cron cannot deactivate itself: the scheduler locks its row
            # and rewrites `active` after the run.
            params.set_param(BACKFILL_PARAM, BACKFILL_DONE)
