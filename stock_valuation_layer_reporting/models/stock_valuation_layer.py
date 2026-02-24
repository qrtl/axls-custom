# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    report_category_id = fields.Many2one(
        "svl.report.category",
    )
    report_category_manually_modified = fields.Boolean(
        compute="_compute_report_category_manually_modified",
        store=True,
    )

    @api.depends("report_category_id")
    def _compute_report_category_manually_modified(self):
        categories = self.env["svl.report.category"].search([])
        for record in self:
            category = record._get_report_category_for_record(categories)
            record.report_category_manually_modified = (
                record.report_category_id != category
            )

    def _get_report_category_for_record(self, categories):
        self.ensure_one()
        other_category = categories.filtered("is_other")
        matches = []
        for cat in categories.filtered(lambda c: not c.is_other):
            try:
                if self.filtered_domain(cat._get_domain()):
                    matches.append(cat)
            except Exception as e:
                _logger.error(
                    "SVL(%s: %s) failed to evaluate domain for report category %s: %s",
                    self.reference,
                    self.product_id.display_name or "",
                    cat.name,
                    e,
                )
        if len(matches) == 0:
            return other_category
        if len(matches) > 1:
            _logger.error(
                "SVL(%s: %s) matched multiple report categories %s",
                self.reference,
                self.product_id.display_name or "",
                matches.mapped("name"),
            )
        return matches[0]

    def assign_report_category(self):
        categories = self.env["svl.report.category"].search([])
        for record in self:
            category = record._get_report_category_for_record(categories)
            if not category:
                continue
            record.write({"report_category_id": category.id})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.assign_report_category()
        return records
