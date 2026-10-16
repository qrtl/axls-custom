# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.tools import float_is_zero, float_round

_logger = logging.getLogger(__name__)

WATERMARK_PARAM = "stock_valuation_fifo_lot_allocation.backfill_last_id"
BALANCED_PARAM = "stock_valuation_fifo_lot_allocation.backfill_balanced"


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
        layers.filtered(lambda x: not x.quantity)._create_lot_allocations()
        return layers

    def _is_lot_allocation_applicable(self):
        self.ensure_one()
        product = self.product_id.with_company(self.company_id)
        return (
            product.cost_method == "fifo"
            and product.tracking != "none"
            and not self.currency_id.is_zero(self.value)
        )

    def _get_value_only_scope_lines(self):
        self.ensure_one()
        move = self.stock_move_id or self.stock_valuation_layer_id.stock_move_id
        if move:
            return move.move_line_ids.filtered(
                lambda x: x.lot_id and x.qty_remaining > 0
            )
        return self.env["stock.move.line"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("company_id", "=", self.company_id.id),
                ("qty_remaining", ">", 0),
            ]
        )

    def _get_lot_allocation_basis(self):
        self.ensure_one()
        basis = defaultdict(float)
        product_uom = self.product_id.uom_id
        if self.quantity > 0:
            for ml in self.stock_move_id.move_line_ids.filtered("lot_id"):
                basis[ml.lot_id] += ml.qty_base
        elif self.quantity < 0:
            # Backfill only: approximate, the residual goes to the balancing pass.
            for ml in self.stock_move_id.move_line_ids.filtered("lot_id"):
                lot = ml.force_fifo_lot_id or ml.lot_id
                basis[lot] += ml.product_uom_id._compute_quantity(
                    ml.qty_done, product_uom
                )
        else:
            for ml in self._get_value_only_scope_lines():
                basis[ml.lot_id] += ml.qty_remaining
        return {lot: qty for lot, qty in basis.items() if qty}

    def _get_lot_allocation_amounts(self, basis=None):
        self.ensure_one()
        if basis is None:
            basis = self._get_lot_allocation_basis()
        total = sum(basis.values())
        if not total:
            return {}
        return {lot: self.value * qty / total for lot, qty in basis.items()}

    def _get_lot_allocation_quantities(self, basis=None):
        self.ensure_one()
        rounding = self.product_id.uom_id.rounding
        if float_is_zero(self.quantity, precision_rounding=rounding):
            return {}
        if basis is None:
            basis = self._get_lot_allocation_basis()
        sign = 1 if self.quantity > 0 else -1
        return {lot: sign * qty for lot, qty in basis.items()}

    def _round_lot_allocation(self, amounts_by_lot):
        self.ensure_one()
        currency = self.currency_id
        amounts = {
            lot: currency.round(amount) for lot, amount in amounts_by_lot.items()
        }
        remainder = currency.round(self.value - sum(amounts.values()))
        if amounts and not currency.is_zero(remainder):
            largest = sorted(amounts, key=lambda lot: (-abs(amounts[lot]), lot.id))[0]
            amounts[largest] += remainder
        return amounts

    def _prepare_lot_allocation_vals(
        self,
        amounts_by_lot,
        quantities_by_lot=None,
        description=None,
        is_opening_adjustment=False,
    ):
        self.ensure_one()
        quantities_by_lot = quantities_by_lot or {}
        rounding = self.product_id.uom_id.rounding
        vals_list = []
        for lot in list(amounts_by_lot) + [
            lot for lot in quantities_by_lot if lot not in amounts_by_lot
        ]:
            amount = amounts_by_lot.get(lot, 0.0)
            quantity = float_round(
                quantities_by_lot.get(lot, 0.0), precision_rounding=rounding
            )
            if self.currency_id.is_zero(amount) and float_is_zero(
                quantity, precision_rounding=rounding
            ):
                continue
            vals_list.append(
                {
                    "lot_id": lot.id,
                    "valuation_layer_id": self.id,
                    "allocated_amount": amount,
                    "allocated_quantity": quantity,
                    "description": description or self.description,
                    "is_opening_adjustment": is_opening_adjustment,
                }
            )
        return vals_list

    def _create_lot_allocations(self, amounts_by_lot=None, quantities_by_lot=None):
        vals_list = []
        for layer in self:
            if not layer._is_lot_allocation_applicable() or layer.lot_allocation_ids:
                continue
            if amounts_by_lot is None:
                basis = layer._get_lot_allocation_basis()
                amounts = layer._get_lot_allocation_amounts(basis)
                quantities = layer._get_lot_allocation_quantities(basis)
            else:
                amounts = amounts_by_lot
                quantities = quantities_by_lot or {}
            vals_list += layer._prepare_lot_allocation_vals(
                layer._round_lot_allocation(amounts), quantities
            )
        return self.env["stock.valuation.lot.allocation"].sudo().create(vals_list)

    @api.model
    def _balance_lot_allocations(self):
        params = self.env["ir.config_parameter"].sudo()
        if params.get_param(BALANCED_PARAM):
            return
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
            if layer.currency_id.is_zero(gap):
                continue
            vals_list += layer._prepare_lot_allocation_vals(
                {self.env["stock.lot"].browse(lot_id): gap},
                description=_("Opening allocation adjustment"),
                is_opening_adjustment=True,
            )
        allocations.create(vals_list)
        params.set_param(BALANCED_PARAM, "1")

    @api.model
    def _get_backfill_watermark(self):
        return int(self.env["ir.config_parameter"].sudo().get_param(WATERMARK_PARAM, 0))

    @api.model
    def _set_backfill_watermark(self, last_id):
        self.env["ir.config_parameter"].sudo().set_param(WATERMARK_PARAM, last_id)

    @api.model
    def _cron_backfill_lot_allocations(self, batch=2000, max_batches=20):
        layers = self.sudo()
        for _batch in range(max_batches):
            svls = layers.search(
                [("id", ">", self._get_backfill_watermark())], order="id", limit=batch
            )
            if not svls:
                self._balance_lot_allocations()
                cron = self.env.ref(
                    "stock_valuation_fifo_lot_allocation."
                    "ir_cron_lot_allocation_backfill",
                    raise_if_not_found=False,
                )
                if cron:
                    cron.active = False
                break
            svls._create_lot_allocations()
            self._set_backfill_watermark(svls[-1].id)
            self.env.cr.commit()  # pylint: disable=invalid-commit
