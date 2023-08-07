# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class InventoryReportWizard(models.TransientModel):
    _name = "inventory.report.wizard"
    _description = "Inventory Report Wizard"

    report_type = fields.Selection(
        [
            ("valuation", "Inventory valuation"),
            ("storable", "Incoming-Outgoing transfers (For storable products)"),
            ("consumable", "Incoming-Outgoing transfers (For consumable products)"),
        ],
        required=True,
        default="valuation",
    )
    date_start = fields.Date("Start Date", required=True)
    date_end = fields.Date("End Date", required=True)

    def export_xlsx(self):
        data = {
            "report_type": self.report_type,
            "date_start": self.date_start,
            "date_end": self.date_end,
        }
        return self.env.ref("inventory_reporting.inventory_report_xlsx").report_action(
            self, data=data
        )
