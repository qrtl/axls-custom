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
        elif data["report_type"] == "consumable":
            self.generate_consumable_report(workbook, wizard)
        else:
            self.generate_summary_report(workbook, wizard)

    def parse_html(self, html_content):
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text()
        return False

    def get_base_domain(self, wizard):
        return [
            ("actual_date", ">=", wizard.date_start),
            ("actual_date", "<=", wizard.date_end),
            ("product_id.active", "=", True),
        ]

    def get_product_categories(self):
        category_objs = self.env["product.category"].search(
            [("is_report_category", "=", True)]
        )
        return category_objs.mapped("name")

    def get_valuation_domain(self, category_name, wizard):
        return [
            ("product_id.active", "=", True),
            ("product_id.categ_id.name", "=", category_name),
            ("actual_date", "<=", wizard.date_end),
        ]

    def generate_valuation_report(self, workbook, wizard):
        categories = self.get_product_categories()
        for _i, category in enumerate(categories):
            ws = workbook.add_worksheet(category)

            # Write the header
            headers = [
                _("Product Name"),
                _("Internal Reference"),
                _("Quantity"),
                _("Unit of Measurement"),
                _("Unit Price"),
                _("Total Value"),
                _("Last Purchase Accounting Date"),
            ]
            column_widths = [25, 20, 10, 20, 12, 15, 30]
            for col, width in enumerate(column_widths):
                ws.set_column(col, col, width)
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            # Fetch the valuation layers for the product category and date range
            valuation_obj = self.env["stock.valuation.layer"]

            # Define search domain
            domain = self.get_valuation_domain(category, wizard)

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
                ws.write(row, 1, product.default_code)
                ws.write(row, 2, valuation_data["quantity"])
                ws.write(row, 3, product.uom_id.name)
                ws.write(row, 4, unit_cost)
                ws.write(row, 5, valuation_data["value"])

                # Convert the date to the desired format (YYYY-MM-DD)
                last_purchase_date = fields.Date.from_string(product.last_purchase_date)
                if last_purchase_date:
                    ws.write(row, 6, last_purchase_date.strftime("%Y-%m-%d"))
                row += 1

    def get_storable_categories(self, wizard):
        base_domain = self.get_base_domain(wizard)
        base_storable_domain = expression.AND(
            [base_domain, [("product_id.detailed_type", "=", "product")]]
        )
        categories = [
            {
                "name": _("Receipt"),
                "filter": [
                    ("stock_move_id.picking_code", "=", "incoming"),
                    ("stock_move_id.origin_returned_move_id", "=", False),
                    ("stock_move_id.unbuild_id", "=", False),
                ],
            },
            {
                "name": _("Return"),  # supplier returns
                "filter": [
                    ("stock_move_id.picking_code", "=", "outgoing"),
                    ("stock_move_id.origin_returned_move_id", "!=", False),
                ],
            },
            {
                "name": _("Component Flush"),
                "filter": [
                    "|",
                    "&",
                    ("stock_move_id.location_dest_id.usage", "=", "production"),
                    (
                        "stock_move_id.location_id.is_subcontracting_location",
                        "=",
                        False,
                    ),
                    "&",
                    ("stock_move_id.location_id.usage", "=", "production"),
                    (
                        "stock_move_id.location_dest_id.is_subcontracting_location",
                        "=",
                        False,
                    ),
                    ("stock_move_id.picking_code", "in", ("internal", "outgoing")),
                    ("stock_move_id.unbuild_id", "=", False),
                    ("stock_move_id.origin_returned_move_id", "=", False),
                ],
            },
            {
                "name": _("Inventory Adjustment"),
                "filter": [
                    "|",
                    ("stock_move_id.location_id.usage", "=", "inventory"),
                    ("stock_move_id.location_dest_id.usage", "=", "inventory"),
                    ("stock_move_id.scrapped", "=", False),
                    ("stock_move_id.unbuild_id", "=", False),
                ],
            },
            {
                "name": _("Scrap"),
                "filter": [
                    ("stock_move_id.scrapped", "=", True),
                ],
            },
            {
                "name": _("Subcontracting"),
                "filter": [
                    "|",
                    "&",
                    (
                        "stock_move_id.location_dest_id.is_subcontracting_location",
                        "=",
                        True,
                    ),
                    ("stock_move_id.location_id.usage", "!=", "inventory"),
                    "&",
                    ("stock_move_id.location_id.is_subcontracting_location", "=", True),
                    ("stock_move_id.location_dest_id.usage", "!=", "inventory"),
                    ("stock_move_id.scrapped", "=", False),
                    ("stock_move_id.unbuild_id", "=", False),
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
        return base_storable_domain, categories

    def setup_storable_worksheet_headers(self, ws):
        headers = [
            _("Reference"),
            _("Origin"),
            _("Actual Date"),
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
        column_widths = [
            15,  # Reference
            15,  # Origin
            15,  # Actual Date
            20,  # Note
            15,  # User
            20,  # Partner
            30,  # Total Amount of Purchase Order
            20,  # Product
            15,  # Product Type
            20,  # Product Category
            25,  # Source Location
            25,  # Destination Location
            10,  # Quantity
            20,  # Unit of Measurement
            25,  # Product Cost Method
            30,  # SVL's Total Inventory Value
            30,  # Analytic Distribution
        ]
        for col, width in enumerate(column_widths):
            ws.set_column(col, col, width)
        for col, header in enumerate(headers):
            ws.write(0, col, header)

    def generate_storable_report(self, workbook, wizard):
        base_storable_domain, categories = self.get_storable_categories(wizard)
        for category in categories:
            ws = workbook.add_worksheet(category["name"])

            # Write the header
            self.setup_storable_worksheet_headers(ws)

            # Fetch the data for the report based on the category and date range
            valuation_obj = self.env["stock.valuation.layer"]
            domain = expression.AND([base_storable_domain, category["filter"]])
            valuations = valuation_obj.search(domain)

            # Write the data to the worksheet
            for row, valuation in enumerate(valuations, start=1):
                actual_date = fields.Date.from_string(valuation.actual_date)
                ws.write(row, 0, valuation.reference)
                ws.write(row, 1, valuation.stock_move_id.origin)
                ws.write(row, 2, actual_date.strftime("%Y-%m-%d"))
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
            self.setup_storable_worksheet_headers(ws)

            # Fetch the data for the report based on the category and date range
            valuation_obj = self.env["stock.valuation.layer"]
            domain = expression.AND([base_consu_domain, category["filter"]])
            valuations = valuation_obj.search(domain)

            # Write the data to the worksheet
            for row, valuation in enumerate(valuations, start=1):
                actual_date = fields.Date.from_string(
                    valuation.stock_move_id.actual_date
                )
                ws.write(row, 0, valuation.reference)
                ws.write(row, 1, valuation.stock_move_id.origin)
                ws.write(row, 2, actual_date.strftime("%Y-%m-%d"))
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

    def generate_summary_report(self, workbook, wizard):
        ws = workbook.add_worksheet(_("Inventory Summary"))
        valuation_obj = self.env["stock.valuation.layer"]
        product_categories = self.get_product_categories()
        base_storable_domain, storable_categories = self.get_storable_categories(wizard)
        headers = [
            _("Product Category"),
            _("Inventory Total Value"),
            _("Inventory Operation Type"),
            _("Operation Type Total Value"),
        ]
        column_widths = [30, 20, 30, 30]
        for col, width in enumerate(column_widths):
            ws.set_column(col, col, width)
        for col, header in enumerate(headers):
            ws.write(0, col, header)
        row = 1
        max_rows = max(len(product_categories), len(storable_categories))
        product_categ_total = 0.0
        inventory_categ_total = 0.0
        for i in range(max_rows):
            if i < len(product_categories):
                category_name = product_categories[i]
                total_value = valuation_obj.read_group(
                    self.get_valuation_domain(category_name, wizard), ["value"], []
                )
                prod_categ_value = (
                    total_value[0]["value"] or 0.0 if total_value else 0.0
                )
                ws.write(row, 0, category_name)
                ws.write(row, 1, prod_categ_value)
                product_categ_total += prod_categ_value
            if i < len(storable_categories):
                cat = storable_categories[i]
                storable_domain = expression.AND([base_storable_domain, cat["filter"]])
                storable_vals = valuation_obj.read_group(storable_domain, ["value"], [])
                inventory_categ_value = (
                    storable_vals[0]["value"] or 0.0 if storable_vals else 0.0
                )
                ws.write(row, 2, cat["name"])
                ws.write(row, 3, inventory_categ_value)
                inventory_categ_total += inventory_categ_value
            row += 1
        row += 1
        ws.write(row, 0, _("Product Category Total"))
        ws.write(row, 1, product_categ_total)
        ws.write(row, 2, _("Inventory Operation Total"))
        ws.write(row, 3, inventory_categ_total)
        row += 2
        ws.write(row, 2, _("Difference"))
        ws.write(row, 3, product_categ_total - inventory_categ_total)
