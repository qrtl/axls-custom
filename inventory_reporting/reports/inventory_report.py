from bs4 import BeautifulSoup

from odoo import _, fields, models


class InventoryReportXlsx(models.AbstractModel):
    _name = "report.inventory_reporting.inventory_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizard):
        report_type = wizard.report_type

        if report_type == "valuation":
            self.generate_valuation_report(workbook, wizard)
        if report_type == "storable":
            self.generate_storable_report(workbook, wizard)
        elif report_type == "consumable":
            self.generate_consumable_report(workbook, wizard)

    def parse_html(self, html_content):
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text()
        return False

    def generate_valuation_report(self, workbook, wizard):
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
                _("Product Name"),
                _("Quantity"),
                _("Unit of Measurement"),
                _("Unit Price"),
                _("Total Value"),
                _("Last Purchase Date"),
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
                if last_purchase_date:
                    ws.write(row, 5, last_purchase_date.strftime("%Y-%m-%d"))

    def generate_storable_report(self, workbook, wizard):
        categories = [
            {
                "name": _("Receipt"),
                "filter": [
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["stock_move_id.picking_type_id.code", "=", "incoming"],
                    ["stock_move_id.origin_returned_move_id", "=", False],
                    ["product_id.detailed_type", "=", "product"],
                ],
            },
            {
                "name": _("Return"),
                "filter": [
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["stock_move_id.origin_returned_move_id", "!=", False],
                    ["reference", "ilike", "/OUT/"],
                    ["product_id.detailed_type", "=", "product"],
                ],
            },
            {
                "name": _("Delivery"),
                "filter": [
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["stock_move_id.picking_type_id.code", "=", "internal"],
                    ["stock_move_id.origin_returned_move_id", "=", False],
                    ["product_id.detailed_type", "=", "product"],
                ],
            },
            {
                "name": _("Inventory Adjustment"),
                "filter": [
                    "&",
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["product_id.detailed_type", "=", "product"],
                    "|",
                    [
                        "stock_move_id.location_id",
                        "ilike",
                        "Virtual Locations/Inventory adjustment",
                    ],
                    [
                        "stock_move_id.location_dest_id",
                        "ilike",
                        "Virtual Locations/Inventory adjustment",
                    ],
                ],
            },
            {
                "name": _("Subcontracting"),
                "filter": [
                    "&",
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["product_id.detailed_type", "=", "product"],
                    "|",
                    [
                        "stock_move_id.location_id",
                        "ilike",
                        "Physical Locations/Subcontracting Location",
                    ],
                    [
                        "stock_move_id.location_dest_id",
                        "ilike",
                        "Physical Locations/Subcontracting Location",
                    ],
                ],
            },
            {
                "name": _("Price Update"),
                "filter": [
                    ["accounting_date", ">=", wizard.date_start],
                    ["accounting_date", "<=", wizard.date_end],
                    ["stock_move_id", "=", False],
                    ["product_id.detailed_type", "=", "product"],
                ],
            },
        ]

        for category in categories:
            ws = workbook.add_worksheet(category["name"])

            # Write the header
            headers = [
                _("Reference"),
                _("Origin"),
                _("Accounting Date"),
                _("Note"),
                _("User"),
                _("Partner"),
                _("Total Amount of Purchase Order"),
                _("Product"),
                _("Product Type"),
                _("Product Category"),
                _("Source Location"),
                _("Destination Location"),
                _("Quantity"),
                _("Unit of Measurement"),
                _("Product Cost Method"),
                _("SVL's Total Inventory Value"),
                _("Analytic Distribution"),
            ]
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            # Fetch the data for the report based on the category and date range
            valuation_obj = self.env["stock.valuation.layer"]
            valuations = valuation_obj.search(category["filter"])

            # Write the data to the worksheet
            for row, valuation in enumerate(valuations, start=1):
                accounting_date = fields.Date.from_string(valuation.accounting_date)
                ws.write(row, 0, valuation.reference)
                ws.write(row, 1, valuation.stock_move_id.origin)
                ws.write(row, 2, accounting_date.strftime("%Y-%m-%d"))
                ws.write(
                    row,
                    3,
                    self.parse_html(valuation.stock_move_id.picking_id.note)
                    if valuation.stock_move_id.picking_id.note
                    else "",
                )
                ws.write(row, 4, valuation.create_uid.name)
                ws.write(row, 5, valuation.stock_move_id.picking_id.partner_id.name)
                ws.write(
                    row, 6, valuation.stock_move_id.purchase_line_id.price_subtotal
                )
                ws.write(row, 7, valuation.product_id.name)
                ws.write(row, 8, valuation.product_id.type)
                ws.write(row, 9, valuation.product_id.categ_id.name)
                ws.write(row, 10, valuation.stock_move_id.location_id.name)
                ws.write(row, 11, valuation.stock_move_id.location_dest_id.name)
                ws.write(row, 12, valuation.quantity)
                ws.write(row, 13, valuation.uom_id.name)
                ws.write(row, 14, valuation.product_id.categ_id.property_cost_method)
                ws.write(row, 15, valuation.value),
                ws.write(
                    row,
                    16,
                    valuation.stock_move_id.analytic_account_names
                    if valuation.stock_move_id.analytic_account_names
                    else "",
                )

    def generate_consumable_report(self, workbook, wizard):
        categories = [
            {
                "name": _("Receipt"),
                "filter": [
                    ["stock_move_id.date", ">=", wizard.date_start],
                    ["stock_move_id.date", "<=", wizard.date_end],
                    ["stock_move_id.picking_type_id.code", "=", "incoming"],
                    ["stock_move_id.origin_returned_move_id", "=", False],
                    ["product_id.detailed_type", "!=", "product"],
                ],
            },
            {
                "name": _("Return"),
                "filter": [
                    ["stock_move_id.date", ">=", wizard.date_start],
                    ["stock_move_id.date", "<=", wizard.date_end],
                    ["stock_move_id.picking_type_id.code", "=", "outgoing"],
                    ["stock_move_id.origin_returned_move_id", "!=", False],
                    ["product_id.detailed_type", "!=", "product"],
                ],
            },
        ]

        for category in categories:
            ws = workbook.add_worksheet(category["name"])

            # Write the header
            headers = [
                _("Reference"),
                _("Origin"),
                _("Accounting Date"),
                _("Note"),
                _("User"),
                _("Partner"),
                _("Total Amount of Purchase Order"),
                _("Product"),
                _("Product Type"),
                _("Product Category"),
                _("Source Location"),
                _("Destination Location"),
                _("Quantity"),
                _("Unit of Measurement"),
                _("Product Cost Method"),
                _("SVL's Total Inventory Value"),
                _("Analytic Distribution"),
            ]
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            # Fetch the data for the report based on the category and date range
            valuation_obj = self.env["stock.valuation.layer"]
            valuations = valuation_obj.search(category["filter"])

            # Write the data to the worksheet
            for row, valuation in enumerate(valuations, start=1):
                date = fields.Date.from_string(valuation.stock_move_id.date)
                ws.write(row, 0, valuation.reference)
                ws.write(row, 1, valuation.stock_move_id.origin)
                ws.write(row, 2, date.strftime("%Y-%m-%d"))
                ws.write(
                    row,
                    3,
                    self.parse_html(valuation.stock_move_id.picking_id.note)
                    if valuation.stock_move_id.picking_id.note
                    else "",
                )
                ws.write(row, 4, valuation.create_uid.name)
                ws.write(row, 5, valuation.stock_move_id.picking_id.partner_id.name)
                ws.write(
                    row, 6, valuation.stock_move_id.purchase_line_id.price_subtotal
                )
                ws.write(row, 7, valuation.product_id.name)
                ws.write(row, 8, valuation.product_id.type)
                ws.write(row, 9, valuation.product_id.categ_id.name)
                ws.write(row, 10, valuation.stock_move_id.location_id.name)
                ws.write(row, 11, valuation.stock_move_id.location_dest_id.name)
                ws.write(row, 12, valuation.quantity)
                ws.write(row, 13, valuation.uom_id.name)
                ws.write(row, 14, valuation.product_id.categ_id.property_cost_method)
                ws.write(row, 15, valuation.value),
                ws.write(
                    row,
                    16,
                    valuation.stock_move_id.analytic_account_names
                    if valuation.stock_move_id.analytic_account_names
                    else "",
                )