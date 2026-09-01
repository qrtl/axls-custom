# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import TransactionCase, tagged

REPORT_NAME = "stock_picking_product_barcode_report.label_barcode_report"


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
                "barcode": "5901234123457",
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "LOT-0001",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
            }
        )

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

    def _count_barcodes(self, html):
        return html.count("/report/barcode/")

    def test_lot_barcode_added(self):
        """A line with a lot gets a second barcode carrying the lot name."""
        html = self._render(self._create_line(lot=self.lot))
        self.assertEqual(self._count_barcodes(html), 2)
        self.assertIn("value=%s" % self.lot.name, html)

    def test_no_lot_no_extra_barcode(self):
        """A line without a lot keeps the single product barcode."""
        html = self._render(self._create_line())
        self.assertEqual(self._count_barcodes(html), 1)

    def test_gs1_format_not_duplicated(self):
        """GS1-128 already encodes the lot, so no second barcode is added."""
        wizard = self.env["stock.picking.print"].create({"barcode_format": "gs1_128"})
        html = self._render(self._create_line(lot=self.lot, wizard=wizard))
        self.assertEqual(self._count_barcodes(html), 1)
        self.assertIn("(10)%s" % self.lot.name, html)
