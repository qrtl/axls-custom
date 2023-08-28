# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import io
import zipfile

from odoo import fields, models


class InventoryReportWizard(models.TransientModel):
    _name = "inventory.report.wizard"
    _description = "Inventory Report Wizard"

    date_start = fields.Date("Start Date", required=True)
    date_end = fields.Date("End Date", required=True)

    def export_xlsx(self):
        # Initialize a byte-stream to hold our ZIP data.
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
            for report_type in ["valuation", "storable", "consumable"]:
                data = {
                    "report_type": report_type,
                    "date_start": self.date_start,
                    "date_end": self.date_end,
                }
                # Obtain Excel data in bytes for the given report type
                report = self.env.ref("inventory_reporting.inventory_report_xlsx")
                excel_content, _ = report._render(
                    report.report_name, [self.id], data=data
                )

                # Add the Excel content to the ZIP file with a unique filename
                if report_type == "valuation":
                    filename = (
                        report_type + "_" + self.date_end.strftime("%Y%m%d") + ".xlsx"
                    )
                else:
                    filename = (
                        report_type
                        + "_"
                        + self.date_start.strftime("%Y%m%d")
                        + "-"
                        + self.date_end.strftime("%Y%m%d")
                        + ".xlsx"
                    )
                zip_file.writestr(filename, excel_content)

        # Convert the ZIP data into base64 for downloading.
        zip_buffer.seek(0)
        zip_data = base64.b64encode(zip_buffer.getvalue())

        # Create an attachment with the ZIP file
        attachment_name = (
            "reports_"
            + self.date_start.strftime("%Y%m%d")
            + "-"
            + self.date_end.strftime("%Y%m%d")
            + ".zip"
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": attachment_name,
                "type": "binary",
                "datas": zip_data,
                "res_model": self._name,
                "res_id": self.id,
            }
        )

        # Return an action to directly download the ZIP.
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }
