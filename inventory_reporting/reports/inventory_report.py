from bs4 import BeautifulSoup

from odoo import _, fields, models
from odoo.osv import expression
from odoo.tools import float_round


class InventoryReportXlsx(models.AbstractModel):
    _name = "report.inventory_reporting.inventory_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizard):
        if data["report_type"] == "valuation":
            self.generate_valuation_report(workbook, wizard)
        elif data["report_type"] == "storable":
            self.generate_storable_report(workbook, wizard)
        else:
            self.generate_consumable_report(workbook, wizard)

    def parse_html(self, html_content):
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text()
        return False

    def get_base_domain(self, wizard):
        return [
            ("accounting_date", ">=", wizard.date_start),
            ("accounting_date", "<=", wizard.date_end),
            ("product_id.active", "=", True),
        ]

    def generate_valuation_report(self, workbook, wizard):
        category_objs = self.env["product.category"].search(
            [("is_report_category", "=", True)]
        )
        categories = category_objs.mapped("name")

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

            # Define search domain
            domain = [
                ("product_id.active", "=", True),
                ("product_id.categ_id.name", "=", category),
                ("accounting_date", "<=", wizard.date_end),
            ]

            # Fields to aggregate
            fields_to_aggregate = ["quantity", "value"]

            valuation_grouped_data = valuation_obj.read_group(
                domain, fields_to_aggregate, ["product_id"]
            )

            # Write the aggregated data
            row = 1
            for valuation_data in valuation_grouped_data:
                product = self.env["product.product"].browse(
                    valuation_data["product_id"][0]
                )
                company_currency = self.env.company.currency_id
                unit_cost = float_round(
                    valuation_data["value"] / valuation_data["quantity"]
                    if valuation_data["quantity"] > 0
                    else 0,
                    precision_rounding=company_currency.rounding,
                    rounding_method="UP",
                )
                ws.write(row, 0, product.name)
                ws.write(row, 1, valuation_data["quantity"])
                ws.write(row, 2, product.uom_id.name)
                ws.write(row, 3, unit_cost)
                ws.write(row, 4, valuation_data["value"])

                # Convert the date to the desired format (YYYY-MM-DD)
                last_purchase_date = fields.Date.from_string(product.last_purchase_date)
                if last_purchase_date:
                    ws.write(row, 5, last_purchase_date.strftime("%Y-%m-%d"))
                row += 1

    def generate_storable_report(self, workbook, wizard):
        base_domain = self.get_base_domain(wizard)
        base_storable_domain = expression.AND(
            [base_domain, [("product_id.detailed_type", "=", "product")]]
        )

        categories = [
            {
                "name": _("Receipt"),
                "filter": [
                    ("stock_move_id.picking_type_id.code", "=", "incoming"),
                    ("stock_move_id.origin_returned_move_id", "=", False),
                ],
            },
            {
                "name": _("Return"),
                "filter": [
                    ("stock_move_id.origin_returned_move_id", "!=", False),
                    ("reference", "ilike", "/OUT/"),
                ],
            },
            {
                "name": _("Delivery"),
                "filter": [
                    ("stock_move_id.picking_type_id.code", "=", "internal"),
                ],
            },
            {
                "name": _("Inventory Adjustment"),
                "filter": [
                    "|",
                    (
                        "stock_move_id.location_id",
                        "ilike",
                        "Virtual Locations/Inventory adjustment",
                    ),
                    (
                        "stock_move_id.location_dest_id",
                        "ilike",
                        "Virtual Locations/Inventory adjustment",
                    ),
                ],
            },
            {
                "name": _("Subcontracting"),
                "filter": [
                    "|",
                    (
                        "stock_move_id.location_id",
                        "ilike",
                        "Physical Locations/Subcontracting Location",
                    ),
                    (
                        "stock_move_id.location_dest_id",
                        "ilike",
                        "Physical Locations/Subcontracting Location",
                    ),
                    ("stock_move_id.unbuild_id", "=", False),
                    "|",
                    (
                        "stock_move_id.production_id",
                        "!=",
                        False,
                    ),
                    ("stock_move_id.raw_material_production_id", "!=", False),
                ],
            },
            {
                "name": _("Price Update"),
                "filter": [
                    ("stock_move_id", "=", False),
                ],
            },
            {
                "name": _("Unbuild"),
                "filter": [
                    ("stock_move_id.unbuild_id", "!=", False),
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
            domain = expression.AND([base_storable_domain, category["filter"]])
            valuations = valuation_obj.search(domain)

            # Write the data to the worksheet
            for row, valuation in enumerate(valuations, start=1):
                accounting_date = fields.Date.from_string(valuation.accounting_date)
                ws.write(row, 0, valuation.reference)
                ws.write(row, 1, valuation.stock_move_id.origin)
                ws.write(row, 2, accounting_date.strftime("%Y-%m-%d"))
                ws.write(
                    row,
                    3,
                    self.parse_html(valuation.stock_move_id.picking_id.note) or "",
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
                    valuation.stock_move_id.analytic_account_names or "",
                )

    def generate_consumable_report(self, workbook, wizard):
        base_domain = self.get_base_domain(wizard)
        base_consu_domain = expression.AND(
            [base_domain, [("product_id.detailed_type", "!=", "product")]]
        )

        categories = [
            {
                "name": _("Receipt"),
                "filter": [
                    ("stock_move_id.picking_type_id.code", "=", "incoming"),
                    ("stock_move_id.origin_returned_move_id", "=", False),
                ],
            },
            {
                "name": _("Return"),
                "filter": [
                    ("stock_move_id.picking_type_id.code", "=", "outgoing"),
                    ("stock_move_id.origin_returned_move_id", "!=", False),
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
            domain = expression.AND([base_consu_domain, category["filter"]])
            valuations = valuation_obj.search(domain)

            # Write the data to the worksheet
            for row, valuation in enumerate(valuations, start=1):
                accounting_date = fields.Date.from_string(
                    valuation.stock_move_id.accounting_date
                )
                ws.write(row, 0, valuation.reference)
                ws.write(row, 1, valuation.stock_move_id.origin)
                ws.write(row, 2, accounting_date.strftime("%Y-%m-%d"))
                ws.write(
                    row,
                    3,
                    self.parse_html(valuation.stock_move_id.picking_id.note) or "",
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
                    valuation.stock_move_id.analytic_account_names or "",
                )
