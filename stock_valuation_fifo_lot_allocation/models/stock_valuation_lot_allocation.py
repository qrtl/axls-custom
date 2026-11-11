# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import api, fields, models


class StockValuationLotAllocation(models.Model):
    _name = "stock.valuation.lot.allocation"
    _description = "Stock Valuation Lot Allocation"
    _order = "actual_date, id"

    lot_id = fields.Many2one(
        "stock.lot",
        "Lot/Serial Number",
        required=True,
        index=True,
        ondelete="cascade",
    )
    valuation_layer_id = fields.Many2one(
        "stock.valuation.layer",
        "Valuation Layer",
        required=True,
        index=True,
        ondelete="cascade",
    )
    allocated_amount = fields.Monetary(
        help="Share of the valuation layer value charged to the lot/serial."
    )
    allocated_quantity = fields.Float(
        digits="Product Unit of Measure",
        help="Share of the valuation layer quantity that belongs to the lot/serial, "
        "in the product UoM and signed as the layer quantity.",
    )
    is_opening_adjustment = fields.Boolean(
        help="Balancing row created by the backfill. It is attached to an incoming "
        "layer of the lot but is not part of that layer's value."
    )
    actual_date = fields.Date(related="valuation_layer_id.actual_date", store=True)
    description = fields.Char()
    product_id = fields.Many2one(related="valuation_layer_id.product_id", store=True)
    product_uom_id = fields.Many2one(related="product_id.uom_id")
    company_id = fields.Many2one(related="valuation_layer_id.company_id", store=True)
    currency_id = fields.Many2one(related="valuation_layer_id.currency_id")

    @api.model
    def _get_lot_gaps(self):
        """Return {lot_id: remaining value - allocated amount}."""
        gaps = defaultdict(float)
        groups = (
            self.env["stock.move.line"]
            .sudo()
            .read_group(
                [("qty_remaining", ">", 0)], ["value_remaining:sum"], ["lot_id"]
            )
        )
        for group in groups:
            if group["lot_id"]:
                gaps[group["lot_id"][0]] += group["value_remaining"]
        for group in self.sudo().read_group([], ["allocated_amount:sum"], ["lot_id"]):
            gaps[group["lot_id"][0]] -= group["allocated_amount"]
        return gaps
