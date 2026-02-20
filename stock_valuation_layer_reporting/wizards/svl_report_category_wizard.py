# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SVLReportCategoryWizard(models.TransientModel):
    _name = "svl.report.category.wizard"
    _description = "SVL Report Category Wizard"

    report_category_id = fields.Many2one(
        "svl.report.category",
        string="Report Category",
        required=True,
    )

    def action_apply(self):
        svls = self.env["stock.valuation.layer"].browse(
            self.env.context.get("active_ids", [])
        )
        if svls:
            svls.write({"report_category_id": self.report_category_id.id})
        return {"type": "ir.actions.act_window_close"}
