# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import get_barcode_check_digit

BASE_REPORT = "stock_picking_product_barcode_report.label_barcode_report"
SHEET_REPORT = "stock_picking_product_barcode_report_gs1_qr.report_stock_qr_label"
ZPL_REPORT = (
    "stock_picking_product_barcode_report_gs1_qr.action_report_stock_qr_label_zpl"
)
QR_IMAGE = "data:image/png;base64,"


@tagged("post_install", "-at_install")
class TestReportLabelBarcodeGS1QR(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env.ref("stock.stock_location_stock")
        cls.plan = cls.env["account.analytic.plan"].create({"name": "Satellite"})
        cls.env.company.barcode_label_analytic_plan_id = cls.plan
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {"name": "AL-LAB-3", "plan_id": cls.plan.id}
        )
        cls.purchase = cls.env["purchase.order"].create(
            {"partner_id": cls.env["res.partner"].create({"name": "Vendor"}).id}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Tracked Product",
                "type": "product",
                "tracking": "lot",
                "default_code": "PUZ6DC-0220-R1",
            }
        )
        cls.shelfinfo = cls.env["product.shelfinfo"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.location.id,
                "area1_id": cls.env["product.shelf.area1"]
                .create({"name": "Workshop/SDG-PS1"})
                .id,
                "area2_id": cls.env["product.shelf.area2"].create({"name": "C14"}).id,
                "position_id": cls.env["product.shelf.position"]
                .create({"name": "手前"})
                .id,
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "GS1QR-0001",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
                "purchase_id": cls.purchase.id,
                "analytic_distribution": {str(cls.analytic_account.id): 100.0},
            }
        )

    @classmethod
    def _free_gtin14(cls):
        # AI (02) is an identifier, so the GS1 parser validates the check digit and
        # the barcode has to be stored zero padded to 14 digits. Product barcodes
        # are unique, so pick one no existing product holds rather than hardcoding
        # a value an installation may already use.
        product = cls.env["product.product"].with_context(active_test=False)
        for counter in range(1000):
            base = "0491234567%03d" % counter
            gtin = base + str(get_barcode_check_digit(base + "0"))
            if not product.search_count([("barcode", "=", gtin)]):
                return gtin
        raise AssertionError("No free GTIN-14 left in the test range")

    def _create_line(self, barcode_format="gs1_qr", lot=None, product=None, **values):
        wizard = self.env["stock.picking.print"].create(
            {"barcode_format": barcode_format}
        )
        return self.env["stock.picking.line.print"].create(
            dict(
                {
                    "product_id": (product or self.product).id,
                    "quantity": 1.0,
                    "label_qty": 1,
                    "uom_id": self.product.uom_id.id,
                    "lot_id": lot.id if lot else False,
                    "wizard_id": wizard.id,
                },
                **values
            )
        )

    def _render(self, report, lines):
        return (
            self.env["ir.actions.report"]
            ._render_qweb_html(report, lines.ids)[0]
            .decode()
        )

    def test_qr_payload_parses_back_to_product_and_lot(self):
        """The printed payload has to survive the nomenclature that reads it.

        This is what pins the FNC1 separator, the AI (240) rule pattern and the
        character set together: drop the separator, or widen the pattern to accept
        "#", and AI (240) swallows the lot element instead of yielding two.
        """
        line = self._create_line(lot=self.lot)
        nomenclature = self.env.ref(
            "barcodes_gs1_nomenclature.default_gs1_nomenclature"
        )
        parsed = nomenclature.parse_barcode(line.gs1_qr_value)
        self.assertEqual(
            [(element["ai"], element["value"]) for element in parsed],
            [("240", self.product.default_code), ("10", self.lot.name)],
        )

    def test_qr_identifies_the_product_by_internal_reference(self):
        """The product goes into AI (240), which resolves to default_code."""
        line = self._create_line(lot=self.lot)
        self.assertFalse(self.product.barcode)
        self.assertEqual(
            line.gs1_qr_value, "240%s#10%s" % (self.product.default_code, self.lot.name)
        )
        self.assertEqual(
            line.gs1_qr_hri,
            "(240)%s(10)%s" % (self.product.default_code, self.lot.name),
        )

    def test_a_product_barcode_never_reaches_the_payload(self):
        """A product barcode must not be encoded, however GTIN-shaped it looks.

        AI (02) validates a check digit, so a barcode that is merely numeric
        makes the whole payload fail to decompose - a label that looks finished
        and that no scanner can read. The internal reference is the identifier.
        """
        # A valid GTIN makes the point strongest: even this one is not encoded.
        self.product.barcode = self._free_gtin14()
        line = self._create_line(lot=self.lot)
        self.assertNotIn(self.product.barcode, line.gs1_qr_value)
        self.assertEqual(
            line.gs1_qr_value, "240%s#10%s" % (self.product.default_code, self.lot.name)
        )

    def test_print_refuses_a_reference_gs1_cannot_encode(self):
        """Printing stops rather than putting an unscannable label on the goods."""
        product = self.env["product.product"].create(
            {"name": "Unencodable", "type": "product", "default_code": "10006049（削除）"}
        )
        line = self._create_line(product=product)
        self.assertFalse(line.gs1_qr_value)
        self.assertIn("10006049（削除）", line.gs1_qr_error)
        with self.assertRaises(UserError):
            line.wizard_id.print_labels()

    def test_print_refuses_a_product_without_an_internal_reference(self):
        """Nothing identifies the stock, so there is nothing to print."""
        product = self.env["product.product"].create(
            {"name": "No reference", "type": "product"}
        )
        line = self._create_line(product=product)
        self.assertTrue(line.gs1_qr_error)
        with self.assertRaises(UserError):
            line.wizard_id.print_labels()

    def test_print_allows_a_line_that_can_be_encoded(self):
        """The guard must not stand in the way of a printable job.

        Without this, a check that raised on every line would look like it
        worked: every test above asserts only that printing is refused.
        """
        line = self._create_line(lot=self.lot)
        self.assertFalse(line.gs1_qr_error)
        self.assertTrue(line.wizard_id.print_labels())

    def test_symbol_is_inlined_in_the_rendered_label(self):
        """The symbol has to be in the document, not fetched while rendering.

        An <img> pointing at /report/barcode renders fine in a browser and fails
        silently under wkhtmltopdf, which prints the alt text and leaves a label
        that looks complete but carries no barcode at all.
        """
        html = self._render(SHEET_REPORT, self._create_line(lot=self.lot))
        self.assertIn(QR_IMAGE, html)
        self.assertNotIn("/report/barcode", html)

    def test_label_carries_purchase_analytic_and_shelf(self):
        """The four sourced fields all reach the rendered label.

        The shelf in particular is the product.shelfinfo generated id, not the
        stock location: locations are warehouse-wide here, so printing one would
        put the same string on every label.
        """
        line = self._create_line(lot=self.lot, location_id=self.location.id)
        html = self._render(SHEET_REPORT, line)
        self.assertIn(self.purchase.name, html)
        self.assertIn(self.analytic_account.name, html)
        self.assertIn(self.lot.name, html)
        self.assertIn("Workshop/SDG-PS1-C14-手前", html)
        self.assertIn(self.product.default_code, html)

    def test_shelf_is_empty_without_a_shelfinfo_record(self):
        """A product with no shelf at that location prints no shelf.

        Falling back to the location would print the warehouse-wide location on
        every such label, which reads like a shelf and is not one.
        """
        other = self.env["stock.location"].create(
            {"name": "B-02", "location_id": self.location.id, "usage": "internal"}
        )
        line = self._create_line(lot=self.lot, location_id=other.id)
        self.assertFalse(line.shelfinfo_id)

    def test_analytic_account_follows_the_configured_plan(self):
        """A lot distributed over several plans shows only the configured one."""
        other_account = self.env["account.analytic.account"].create(
            {
                "name": "Other plan account",
                "plan_id": self.env["account.analytic.plan"]
                .create({"name": "Project"})
                .id,
            }
        )
        self.lot.analytic_distribution = {
            str(self.analytic_account.id): 50.0,
            str(other_account.id): 50.0,
        }
        line = self._create_line(lot=self.lot)
        self.assertEqual(line.analytic_account_id, self.analytic_account)

    def test_bulk_print_from_a_shelf(self):
        """Selecting shelf records collects the quants sitting on them."""
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.location, 2.0, lot_id=self.lot
        )
        wizard = (
            self.env["stock.picking.print"]
            .with_context(
                active_model="product.shelfinfo", active_ids=self.shelfinfo.ids
            )
            .create({"barcode_format": "gs1_qr"})
        )
        line = wizard.product_print_moves
        self.assertEqual(len(line), 1)
        self.assertEqual(line.shelfinfo_id, self.shelfinfo)
        self.assertEqual(line.lot_id, self.lot)

    def test_bulk_print_from_a_location(self):
        """Selecting a location collects every quant stored below it."""
        shelf = self.env["stock.location"].create(
            {"name": "A-01", "location_id": self.location.id, "usage": "internal"}
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product, shelf, 3.0, lot_id=self.lot
        )
        wizard = (
            self.env["stock.picking.print"]
            .with_context(active_model="stock.location", active_ids=self.location.ids)
            .create({"barcode_format": "gs1_qr"})
        )
        line = wizard.product_print_moves.filtered(
            lambda line: line.product_id == self.product
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.location_id, shelf)
        self.assertEqual(line.lot_id, self.lot)

    def test_receipt_lines_are_listed_whatever_the_product_carries(self):
        """The base report keeps only products with a barcode; the QR label needs
        every line, so that the ones it cannot print are named rather than gone."""
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.env.ref(
                                "stock.stock_location_suppliers"
                            ).id,
                            "location_dest_id": self.location.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.move_line_ids.lot_id = self.lot
        wizard = self.env["stock.picking.print"].create(
            {"barcode_format": "gs1_qr", "picking_ids": [(6, 0, picking.ids)]}
        )
        wizard._onchange_picking_ids()
        self.assertEqual(wizard.product_print_moves.product_id, self.product)
        # The receipt destination is the location the shelves are keyed on, so a
        # label printed at receipt already carries the shelf.
        self.assertEqual(wizard.product_print_moves.shelfinfo_id, self.shelfinfo)

    def test_sheet_breaks_pages_at_the_grid_size(self):
        """Labels past the 40th cell start a new sheet instead of overflowing."""
        line = self._create_line(lot=self.lot, label_qty=41)
        pages = line._get_label_pages()
        self.assertEqual([len(page) for page in pages], [10, 1])
        self.assertEqual([len(row) for row in pages[0]], [4] * 10)
        self.assertEqual([len(row) for row in pages[1]], [1])

    def test_gs1_128_still_prints_1d(self):
        """The existing GS1-128 format is left alone."""
        self.product.barcode = self._free_gtin14()
        html = self._render(BASE_REPORT, self._create_line("gs1_128", lot=self.lot))
        self.assertIn("barcode_type=gs1_128", html)
        self.assertNotIn("barcode_type=QR", html)

    def test_format_available_as_company_default(self):
        """The option can be set as the company default."""
        self.env.company.barcode_report_default_format = "gs1_qr"
        wizard = self.env["stock.picking.print"].create({})
        self.assertEqual(wizard.barcode_format, "gs1_qr")

    # -- the same label, printed as ZPL on a roll rather than on an A4 sheet --

    def _render_zpl(self, lines):
        content, _content_type = self.env["ir.actions.report"]._render_qweb_text(
            self.env.ref(ZPL_REPORT), lines.ids
        )
        return content

    def _zpl_wizard(self, line):
        """Point the line's wizard at the ZPL report.

        Not "gs1_qr": that format alone already routes a line through the
        refusal check, which would hide whether selecting the report does so.
        """
        line.wizard_id.write(
            {
                "barcode_format": "gs1_128",
                "barcode_report": self.env.ref(ZPL_REPORT).id,
            }
        )
        return line

    def test_zpl_is_one_block_per_label_copy(self):
        """A roll printer takes a flat stream, so label_qty is the block count."""
        line = self._create_line(lot=self.lot, label_qty=3)
        zpl = self._render_zpl(line).decode("cp932")
        self.assertEqual(zpl.count("^XA"), 3)
        self.assertEqual(zpl.count("^XZ"), 3)

    def test_zpl_carries_the_same_fields_as_the_sheet(self):
        """The ZPL output is a second medium, not a second label."""
        line = self._create_line(lot=self.lot, location_id=self.location.id)
        zpl = self._render_zpl(line).decode("cp932")
        self.assertIn(self.product.default_code, zpl)
        self.assertIn(self.product.name, zpl)
        self.assertIn(self.purchase.name, zpl)
        self.assertIn(self.analytic_account.name, zpl)
        self.assertIn(self.lot.name, zpl)
        self.assertIn("Workshop/SDG-PS1-C14-手前", zpl)
        self.assertIn("^BQN,2,3^FDMA,%s^FS" % line.gs1_qr_value, zpl)

    def test_zpl_stream_reaches_the_printer_as_cp932(self):
        """^CI15 selects Shift-JIS on the printer, so UTF-8 would be mojibake."""
        content = self._render_zpl(
            self._create_line(lot=self.lot, location_id=self.location.id)
        )
        self.assertIn("手前".encode("cp932"), content)
        self.assertNotIn("手前".encode("utf-8"), content)
        self.assertIn(b"\r\n", content)

    def test_zpl_neutralises_a_caret_in_free_text(self):
        """ZPL reads ^ as a command introducer even inside ^FD."""
        product = self.env["product.product"].create(
            {
                "name": "Bracket ^FS injected",
                "type": "product",
                "default_code": "CARET-0001",
            }
        )
        zpl = self._render_zpl(self._create_line(product=product)).decode("cp932")
        self.assertIn("Bracket  FS injected", zpl)
        self.assertNotIn("Bracket ^FS injected", zpl)

    def test_zpl_print_refuses_a_line_that_cannot_be_encoded(self):
        """Selecting the ZPL report must refuse exactly what the sheet refuses."""
        product = self.env["product.product"].create(
            {"name": "No reference", "type": "product"}
        )
        line = self._zpl_wizard(self._create_line(product=product))
        self.assertTrue(line.gs1_qr_error)
        with self.assertRaises(UserError):
            line.wizard_id.print_labels()

    def test_zpl_print_allows_a_line_that_can_be_encoded(self):
        """Guards the test above: it would pass on a wizard that never prints."""
        line = self._zpl_wizard(self._create_line(lot=self.lot))
        self.assertFalse(line.gs1_qr_error)
        self.assertTrue(line.wizard_id.print_labels())

    def test_a_lot_alone_is_not_an_identification(self):
        """A payload of AI (10) only names a lot of nothing in particular.

        The product has to be identified whatever else is on the label, so the
        rule is "there must be an AI (240) element", not "there must be some
        element" - a product with no internal reference but with a lot used to
        slip through and print a code that resolves to no product.
        """
        product = self.env["product.product"].create(
            {"name": "No reference", "type": "product"}
        )
        line = self._create_line(product=product, lot=self.lot)
        self.assertTrue(line.gs1_qr_error)
        self.assertFalse(line.gs1_qr_value)
