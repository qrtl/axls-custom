# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    report_category = fields.Many2one(
        "svl.report.category",
    )

    def _get_default_report_category(self):
        self.ensure_one()
        categories = self.env["svl.report.category"].search(
            [("active", "=", True)], order="sequence,id"
        )
        other_category = categories.filtered("is_other")[:1]
        matches = []
        for category in categories:
            if category.is_other:
                continue
            domain = category._get_domain()
            if self.filtered_domain(domain):
                matches.append(category)
        if len(matches) == 1:
            return matches[0]
        return other_category

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for vals, record in zip(vals_list, records):
            if not vals.get("report_category"):
                record.report_category = record._get_default_report_category()
        return records
