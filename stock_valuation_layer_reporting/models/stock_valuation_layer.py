# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    default_report_category = fields.Many2one(
        "svl.report.category",
    )

    report_category = fields.Many2one(
        "svl.report.category",
    )

    def _get_report_category_for_record(self, categories, other_category):
        self.ensure_one()
        matches = []
        for category in categories:
            if category.is_other:
                continue
            if self.filtered_domain(category._get_domain()):
                matches.append(category)
        return matches[0] if len(matches) == 1 else other_category

    def apply_report_category_defaults(self):
        """
        レコードにレポートカテゴリのデフォルト値を適用する。

        有効なすべてのレポートカテゴリを取得し、各レコードに対して
        適切なカテゴリを決定して割り当てる。デフォルトカテゴリが
        未設定の場合は同時に設定する。

        Returns:
            None
        """
        categories = self.env["svl.report.category"].search(
            [("active", "=", True)], order="sequence,id"
        )
        other_category = categories.filtered("is_other")[:1]
        for record in self:
            category_value = record._get_report_category_for_record(
                categories, other_category
            )
            if not category_value:
                continue
            vals = {"report_category": category_value.id}
            if not record.default_report_category:
                vals["default_report_category"] = category_value.id
            record.write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.apply_report_category_defaults()
        return records
