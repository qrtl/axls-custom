# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import TransactionCase, tagged
from odoo.tools import get_barcode_check_digit

REPORT_NAME = "stock_picking_product_barcode_report.label_barcode_report"


@tagged("post_install", "-at_install")
class TestReportLabelBarcodeGS1QR(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # AI (02) is an identifier, so the GS1 parser validates the check digit
        # and the barcode has to be stored zero padded to 14 digits. Product
        # barcodes are unique, so pick one that no existing product holds
        # rather than hardcoding a value an installation may already use.
        cls.gtin = cls._free_gtin14()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Tracked Product",
                "type": "product",
                "tracking": "lot",
                "barcode": cls.gtin,
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "GS1QR-0001",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
            }
        )

    @classmethod
    def _free_gtin14(cls):
        product = cls.env["product.product"].with_context(active_test=False)
        for counter in range(1000):
            base = "0491234567%03d" % counter
            gtin = base + str(get_barcode_check_digit(base + "0"))
            if not product.search_count([("barcode", "=", gtin)]):
                return gtin
        raise AssertionError("No free GTIN-14 left in the test range")

    def _create_line(self, barcode_format, lot=None, product=None):
        wizard = self.env["stock.picking.print"].create(
            {"barcode_format": barcode_format}
        )
        return self.env["stock.picking.line.print"].create(
            {
                "product_id": (product or self.product).id,
                "quantity": 1.0,
                "label_qty": 1,
                "uom_id": self.product.uom_id.id,
                "lot_id": lot.id if lot else False,
                "wizard_id": wizard.id,
            }
        )

    def _render(self, line):
        return (
            self.env["ir.actions.report"]
            ._render_qweb_html(REPORT_NAME, line.ids)[0]
            .decode()
        )

    def test_qr_carries_product_and_lot(self):
        """The QR code encodes the same GS1 payload as the GS1-128 barcode."""
        html = self._render(self._create_line("gs1_qr", lot=self.lot))
        self.assertIn("barcode_type=QR", html)
        self.assertIn("value=02%s10%s&" % (self.gtin, self.lot.name), html)
        self.assertIn("(02)%s(10)%s" % (self.gtin, self.lot.name), html)
        # A QR code printed without its quiet zone does not decode.
        self.assertIn("quiet=0", html)
        # The 1D symbol must not be printed as well.
        self.assertNotIn("barcode_type=gs1_128", html)

    def test_qr_without_lot(self):
        """Without a lot the payload carries AI (02) only."""
        html = self._render(self._create_line("gs1_qr"))
        self.assertIn("value=02%s&" % self.gtin, html)
        self.assertNotIn("(10)", html)

    def test_qr_without_product_barcode(self):
        """No GTIN means no symbol, rather than one encoding all zeros."""
        product = self.env["product.product"].create(
            {"name": "Test Product Without Barcode", "type": "product"}
        )
        html = self._render(self._create_line("gs1_qr", product=product))
        self.assertNotIn("/report/barcode/", html)

    def test_gs1_128_still_prints_1d(self):
        """The existing GS1-128 format is left alone."""
        html = self._render(self._create_line("gs1_128", lot=self.lot))
        self.assertIn("barcode_type=gs1_128", html)
        self.assertNotIn("barcode_type=QR", html)

    def test_format_available_as_company_default(self):
        """The option can be set as the company default."""
        self.env.company.barcode_report_default_format = "gs1_qr"
        wizard = self.env["stock.picking.print"].create({})
        self.assertEqual(wizard.barcode_format, "gs1_qr")
