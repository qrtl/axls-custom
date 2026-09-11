# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from markupsafe import escape

from odoo.tests import TransactionCase, tagged
from odoo.tools import get_barcode_check_digit

REPORT_NAME = "stock_picking_product_barcode_report.label_barcode_report"
INLINE_SYMBOL = "data:image/png;base64,"


@tagged("post_install", "-at_install")
class TestReportLabelBarcodeLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Tracked Product",
                "type": "product",
                "tracking": "lot",
                # 13 digits so the base template takes its EAN13 branch, which is
                # the one an existing installation is most likely to be printing.
                "barcode": cls._free_ean13(),
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "LOT-0001",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
            }
        )

    @classmethod
    def _free_ean13(cls):
        # Product barcodes are unique, so pick one no existing product holds
        # rather than hardcoding a value the installation may already use.
        product = cls.env["product.product"].with_context(active_test=False)
        for counter in range(1000):
            base = "590123412%03d" % counter
            ean = base + str(get_barcode_check_digit(base + "0"))
            if not product.search_count([("barcode", "=", ean)]):
                return ean
        raise AssertionError("No free EAN-13 left in the test range")

    def _create_line(self, lot=None, wizard=None):
        return self.env["stock.picking.line.print"].create(
            {
                "product_id": self.product.id,
                "quantity": 1.0,
                "label_qty": 1,
                "uom_id": self.product.uom_id.id,
                "lot_id": lot.id if lot else False,
                "wizard_id": wizard.id if wizard else False,
            }
        )

    def _render(self, line):
        html = self.env["ir.actions.report"]._render_qweb_html(REPORT_NAME, line.ids)[0]
        return html.decode()

    def _count_lot_barcodes(self, html):
        # The lot symbol is inlined by the barcode widget; the base module's own
        # product barcode is still an <img> pointing at /report/barcode.
        return html.count(INLINE_SYMBOL)

    def test_lot_barcode_added(self):
        """A line with a lot gets a second barcode carrying the lot name."""
        html = self._render(self._create_line(lot=self.lot))
        self.assertEqual(self._count_lot_barcodes(html), 1)
        self.assertEqual(html.count("/report/barcode/"), 1)
        self.assertIn("Barcode %s" % self.lot.name, html)

    def test_no_lot_no_extra_barcode(self):
        """A line without a lot keeps the single product barcode."""
        html = self._render(self._create_line())
        self.assertEqual(self._count_lot_barcodes(html), 0)
        self.assertEqual(html.count("/report/barcode/"), 1)

    def test_gs1_format_not_duplicated(self):
        """GS1-128 already encodes the lot, so no second barcode is added."""
        wizard = self.env["stock.picking.print"].create({"barcode_format": "gs1_128"})
        html = self._render(self._create_line(lot=self.lot, wizard=wizard))
        self.assertEqual(self._count_lot_barcodes(html), 0)
        self.assertIn("(10)%s" % self.lot.name, html)

    def test_lot_barcode_encodes_the_whole_name(self):
        """The symbol has to be built from the lot name, not from a URL holding it.

        Splicing the name into a /report/barcode query cut it at the first "#",
        so the printed symbol encoded a different value than the text beside it -
        and the label looked perfectly correct. "&", "+" and spaces did the same.
        """
        lot = self.env["stock.lot"].create(
            {
                "name": "A#1&2 3",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
            }
        )
        html = self._render(self._create_line(lot=lot))
        # The widget derives its alt text from the value it encoded, so a
        # truncated value shows up here as "Barcode A".
        self.assertIn("Barcode %s" % escape(lot.name), html)
        self.assertNotIn("/report/barcode/?barcode_type=Code128", html)
