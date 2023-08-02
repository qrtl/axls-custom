# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class InventoryTransferReportWizard(models.TransientModel):
    _name = "inventory.transfer.report.wizard"
    _description = "Inventory Transfer Report Wizard"

    report_type = fields.Selection(
        [("storable", "Storable Products"), ("consumable", "Consumable Products")],
        required=True,
        default="storable",
    )
    date_start = fields.Date("Start Date", required=True)
    date_end = fields.Date("End Date", required=True)

    def export_xlsx(self):
        data = {
            "report_type": self.report_type,
            "date_start": self.date_start,
            "date_end": self.date_end,
        }
        return self.env.ref(
            "inventory_reporting.inventory_transfer_report_xlsx"
        ).report_action(self, data=data)
