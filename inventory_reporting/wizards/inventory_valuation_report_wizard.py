# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class InventoryValuationReportWizard(models.TransientModel):
    _name = "inventory.valuation.report.wizard"

    date_start = fields.Date("Start Date", required=True)
    date_end = fields.Date("End Date", required=True)

    def export_xlsx(self):
        data = {
            "date_start": self.date_start,
            "date_end": self.date_end,
        }
        return self.env.ref(
            "inventory_reporting.inventory_valuation_report_xlsx"
        ).report_action(self, data=data)
