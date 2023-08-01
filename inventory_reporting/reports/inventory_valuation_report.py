from odoo import fields, models


class InventoryReportXlsx(models.AbstractModel):
    _name = "report.inventory_reporting.inventory_valutaion_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizard):
        categories = [
            "Harness",
            "PCBA",
            "PCB",
            "Electrical",
            "Component",
            "Mechanical",
            "Consumable",
        ]

        for _i, category in enumerate(categories):
            ws = workbook.add_worksheet(category)

            # Write the header
            headers = [
                "Product Name (プロダクト名)",
                "Quantity (個数)",
                "Unit of Measurement (単位)",
                "Unit Price (単価)",
                "Total Value (合計価値)",
                "Last Purchase Date (最終購入日)",
            ]
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            # Fetch the valuation layers for the product category and date range
            valuation_obj = self.env["stock.valuation.layer"]
            valuations = valuation_obj.search(
                [
                    ("product_id.categ_id.name", "=", category),
                    ("accounting_date", ">=", wizard.date_start),
                    ("accounting_date", "<=", wizard.date_end),
                ]
            )

            # Write the data
            for row, valuation in enumerate(valuations, start=1):
                ws.write(row, 0, valuation.product_id.name)
                ws.write(row, 1, valuation.quantity)
                ws.write(row, 2, valuation.product_id.uom_id.name)
                ws.write(row, 3, valuation.unit_cost)
                ws.write(row, 4, valuation.value)

                # Convert the date to the desired format (YYYY-MM-DD)
                last_purchase_date = fields.Date.from_string(
                    valuation.product_id.last_purchase_date
                )
                ws.write(row, 5, last_purchase_date.strftime("%Y-%m-%d"))
