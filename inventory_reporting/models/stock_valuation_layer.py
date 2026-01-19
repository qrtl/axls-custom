# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    report_category = fields.Selection(
        [
            ("receipt", _("Receipt")),
            ("vendor_return", _("Vendor Return")),
            ("component_flush", _("Component Flush")),
            ("component_return", _("Component Return")),
            ("inventory_adjustment", _("Inventory Adjustment")),
            ("scrap", _("Scrap")),
            ("subcontracting", _("Subcontracting")),
            ("price_update", _("Price Update")),
            ("unbuild", _("Unbuild")),
            ("other", _("Other")),
            ("non_product", _("Non-product (Excluded)")),
        ],
        string="Report Category",
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for vals, record in zip(vals_list, records):
            if not vals.get("report_category"):
                record.report_category = record._get_default_report_category()
        return records

    def _get_default_report_category(self):
        self.ensure_one()
        if not self.stock_move_id:
            return "price_update"
        if self.product_id and self.product_id.detailed_type != "product":
            picking_code = self.stock_move_id.picking_type_id.code
            if picking_code == "incoming":
                return "receipt"
            if picking_code == "outgoing":
                return "vendor_return"
            return "non_product"
        matched_categories = []
        for category_key, domain in self._get_report_category_domains():
            if self.filtered_domain(domain):
                matched_categories.append(category_key)
                if len(matched_categories) > 1:
                    return "other"
        if len(matched_categories) == 1:
            return matched_categories[0]
        return "other"

    def _get_report_category_domains(self):
        return [
            (
                "receipt",
                [
                    ("stock_move_id.picking_code", "=", "incoming"),
                    ("stock_move_id.origin_returned_move_id", "=", False),
                    ("stock_move_id.unbuild_id", "=", False),
                ],
            ),
            (
                "vendor_return",
                [
                    ("stock_move_id.picking_code", "=", "outgoing"),
                    ("stock_move_id.origin_returned_move_id", "!=", False),
                ],
            ),
            (
                "component_flush",
                [
                    ("stock_move_id.location_dest_id.usage", "=", "production"),
                    ("stock_move_id.location_id.is_subcontracting_location", "=", False),
                    ("stock_move_id.origin_returned_move_id", "=", False),
                    ("stock_move_id.picking_code", "in", ("internal", "outgoing")),
                    ("stock_move_id.unbuild_id", "=", False),
                ],
            ),
            (
                "component_return",
                [
                    ("stock_move_id.location_dest_id.is_subcontracting_location", "=", False),
                    ("stock_move_id.location_id.usage", "=", "production"),
                    ("stock_move_id.unbuild_id", "=", False),
                ],
            ),
            (
                "inventory_adjustment",
                [
                    "|",
                    ("stock_move_id.location_id.usage", "=", "inventory"),
                    ("stock_move_id.location_dest_id.usage", "=", "inventory"),
                    ("stock_move_id.scrapped", "=", False),
                    ("stock_move_id.unbuild_id", "=", False),
                ],
            ),
            (
                "scrap",
                [
                    ("stock_move_id.scrapped", "=", True),
                ],
            ),
            (
                "subcontracting",
                [
                    "|",
                    "&",
                    (
                        "stock_move_id.location_dest_id.is_subcontracting_location",
                        "=",
                        True,
                    ),
                    ("stock_move_id.location_id.usage", "!=", "inventory"),
                    "&",
                    ("stock_move_id.location_id.is_subcontracting_location", "=", True),
                    ("stock_move_id.location_dest_id.usage", "!=", "inventory"),
                    ("stock_move_id.scrapped", "=", False),
                    ("stock_move_id.unbuild_id", "=", False),
                ],
            ),
            (
                "unbuild",
                [
                    ("stock_move_id.unbuild_id", "!=", False),
                ],
            ),
        ]
