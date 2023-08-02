from odoo import fields, models


class InventoryTransferReportXlsx(models.AbstractModel):
    _name = "report.inventory_reporting.inventory_transfer_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizard):
        report_type = wizard.report_type

        if report_type == "storable":
            self.generate_storable_report(workbook, wizard)
        elif report_type == "consumable":
            self.generate_consumable_report(workbook, wizard)

    def generate_storable_report(self, workbook, wizard):
        categories = [
            {
                "name": "Receipt",
                "filter": [
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["product_id.active", "=", True],
                    ["reference", "ilike", "/IN/"],
                    ["product_id.detailed_type", "=", "product"],
                ],
            },
            {
                "name": "Return",
                "filter": [
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["product_id.active", "=", True],
                    ["reference", "ilike", "/OUT/"],
                    ["product_id.detailed_type", "=", "product"],
                ],
            },
        ]

        for category in categories:
            ws = workbook.add_worksheet(category["name"])

            # Write the header
            headers = [
                "Reference",
                "Origin",
                "Accounting Date",
                "Note",
                "User",
                "Partner",
                "Total Amount of Purchase Order",
                "Product",
                "Product Type",
                "Product Category",
                "Source Location",
                "Destination Location",
                "Quantity",
                "Unit of Measurement",
                "Product Cost Method",
                "SVL's Total Inventory Value",
                "Analytic Distribution",
            ]
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            # Fetch the data for the report based on the category and date range
            move_obj = self.env["stock.move"]
            moves = move_obj.search(category["filter"])

            # Write the data to the worksheet
            for row, move in enumerate(moves, start=1):
                accounting_date = fields.Date.from_string(move.accounting_date)
                ws.write(row, 0, move.reference)
                ws.write(row, 1, move.origin)
                ws.write(row, 2, accounting_date)
                ws.write(row, 3, "")
                ws.write(row, 4, move.create_uid.name)
                ws.write(row, 5, move.partner_id.name)
                ws.write(row, 6, "")
                ws.write(row, 7, move.product_id.name)
                ws.write(row, 8, move.product_id.type)
                ws.write(row, 9, move.product_id.categ_id.name)
                ws.write(row, 10, move.location_id.name)
                ws.write(row, 11, move.location_dest_id.name)
                ws.write(row, 12, move.quantity_done)
                ws.write(row, 13, move.product_uom.name)
                ws.write(row, 14, move.product_id.categ_id.property_cost_method)
                ws.write(row, 15, "")
                ws.write(
                    row,
                    16,
                    move.analytic_account_names if move.analytic_account_names else "",
                )

    def generate_consumable_report(self, workbook, wizard):
        categories = [
            {
                "name": "Receipt",
                "filter": [
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["product_id.active", "=", True],
                    ["name", "ilike", "/IN/"],
                    ["product_id.detailed_type", "!=", "product"],
                ],
            },
            {
                "name": "Return",
                "filter": [
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["product_id.active", "=", True],
                    ["name", "ilike", "/OUT/"],
                    ["product_id.detailed_type", "!=", "product"],
                ],
            },
        ]

        for category in categories:
            ws = workbook.add_worksheet(category["name"])

            # Write the header
            headers = [
                "Reference",
                "Origin",
                "Accounting Date",
                "Note",
                "User",
                "Partner",
                "Total Amount of Purchase Order",
                "Product",
                "Product Type",
                "Product Category",
                "Source Location",
                "Destination Location",
                "Quantity",
                "Unit of Measurement",
                "Product Cost Method",
                "SVL's Total Inventory Value",
                "Analytic Distribution",
            ]
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            # Fetch the data for the report based on the category and date range
            move_obj = self.env["stock.move"]
            moves = move_obj.search(category["filter"])

            # Write the data to the worksheet
            for row, move in enumerate(moves, start=1):
                accounting_date = fields.Date.from_string(move.accounting_date)
                ws.write(row, 0, move.reference)
                ws.write(row, 1, move.origin)
                ws.write(row, 2, accounting_date)
                ws.write(row, 3, "")
                ws.write(row, 4, move.create_uid.name)
                ws.write(row, 5, move.partner_id.name)
                ws.write(row, 6, "")
                ws.write(row, 7, move.product_id.name)
                ws.write(row, 8, move.product_id.type)
                ws.write(row, 9, move.product_id.categ_id.name)
                ws.write(row, 10, move.location_id.name)
                ws.write(row, 11, move.location_dest_id.name)
                ws.write(row, 12, move.quantity_done)
                ws.write(row, 13, move.product_uom.name)
                ws.write(row, 14, move.product_id.categ_id.property_cost_method)
                ws.write(row, 15, "")
                ws.write(
                    row,
                    16,
                    move.analytic_account_names if move.analytic_account_names else "",
                )
