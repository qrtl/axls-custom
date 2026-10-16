# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.tools import float_compare


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
    def _get_lot_gaps(self, company_ids=None):
        ml_domain = [("qty_remaining", ">", 0)]
        allocation_domain = []
        if company_ids is not None:
            ml_domain.append(("company_id", "in", company_ids))
            allocation_domain.append(("company_id", "in", company_ids))
        gaps = defaultdict(float)
        groups = (
            self.env["stock.move.line"]
            .sudo()
            .read_group(ml_domain, ["value_remaining:sum"], ["lot_id"])
        )
        for group in groups:
            if group["lot_id"]:
                gaps[group["lot_id"][0]] += group["value_remaining"]
        groups = self.sudo().read_group(
            allocation_domain, ["allocated_amount:sum"], ["lot_id"]
        )
        for group in groups:
            gaps[group["lot_id"][0]] -= group["allocated_amount"]
        return gaps

    @api.model
    def _get_integrity_issues(self):
        issues = []
        company_ids = self.env.companies.ids
        groups = self.sudo().read_group(
            [("is_opening_adjustment", "=", False), ("company_id", "in", company_ids)],
            ["allocated_amount:sum"],
            ["valuation_layer_id"],
        )
        layers = self.env["stock.valuation.layer"].sudo()
        for group in groups:
            layer = layers.browse(group["valuation_layer_id"][0])
            if not layer.currency_id.is_zero(layer.value - group["allocated_amount"]):
                issues.append(
                    {
                        "check": "layer",
                        "record": layer,
                        "expected": layer.value,
                        "allocated": group["allocated_amount"],
                    }
                )
        lots = self.env["stock.lot"].sudo()
        for lot_id, gap in self._get_lot_gaps(company_ids=company_ids).items():
            lot = lots.browse(lot_id)
            currency = lot.company_id.currency_id or self.env.company.currency_id
            if (
                float_compare(
                    abs(gap), currency.rounding, precision_rounding=currency.rounding
                )
                > 0
            ):
                allocated = sum(
                    self.sudo()
                    .search([("lot_id", "=", lot_id)])
                    .mapped("allocated_amount")
                )
                issues.append(
                    {
                        "check": "lot",
                        "record": lot,
                        "expected": allocated + gap,
                        "allocated": allocated,
                    }
                )
        return issues

    @api.model
    def action_check_integrity(self):
        issues = self._get_integrity_issues()
        if not issues:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Lot Allocation Integrity"),
                    "message": _("All layers and lots reconcile."),
                    "type": "success",
                },
            }
        lines = []
        for issue in issues[:20]:
            label = (
                _("Layer %s") if issue["check"] == "layer" else _("Lot %s")
            ) % issue["record"].display_name
            lines.append(
                _("%(label)s: expected %(expected).2f, allocated %(allocated).2f")
                % {
                    "label": label,
                    "expected": issue["expected"],
                    "allocated": issue["allocated"],
                }
            )
        if len(issues) > 20:
            lines.append(_("... and %s more.") % (len(issues) - 20))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Lot Allocation Integrity: %s issue(s)") % len(issues),
                "message": "\n".join(lines),
                "type": "warning",
                "sticky": True,
            },
        }
