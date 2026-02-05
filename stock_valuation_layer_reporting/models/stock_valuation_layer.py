# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    report_category = fields.Many2one(
        "svl.report.category",
    )
    report_category_changed = fields.Boolean(
        compute="_compute_report_category_changed",
        store=True,
    )

    @api.depends("report_category")
    def _compute_report_category_changed(self):
        categories = self.env["svl.report.category"].search([])
        for record in self:
            category_value = record._get_report_category_for_record(categories)
            record.report_category_changed = record.report_category != category_value

    def _get_report_category_for_record(self, categories):
        self.ensure_one()
        other_category = categories.filtered("is_other")[:1]
        matches = []
        for category in categories.filtered(lambda c: not c.is_other):
            if self.filtered_domain(category._get_domain()):
                matches.append(category)
        return matches[0] if len(matches) == 1 else other_category

    def apply_report_category_defaults(self):
        categories = self.env["svl.report.category"].search([])
        for record in self:
            category_value = record._get_report_category_for_record(categories)
            if not category_value:
                continue
            record.write({"report_category": category_value.id})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.apply_report_category_defaults()
        return records
