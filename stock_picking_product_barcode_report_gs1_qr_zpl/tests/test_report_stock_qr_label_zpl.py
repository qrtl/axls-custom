# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

ZPL_REPORT = (
    "stock_picking_product_barcode_report_gs1_qr_zpl.action_report_stock_qr_label_zpl"
)


@tagged("post_install", "-at_install")
class TestReportStockQRLabelZPL(TransactionCase):
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

    def _create_line(self, product=None, lot=None, **values):
        wizard = self.env["stock.picking.print"].create(
            {
                # Not "gs1_qr": that format alone already routes a line through
                # the refusal check, which would hide whether selecting the ZPL
                # report does so on its own.
                "barcode_format": "gs1_128",
                "barcode_report": self.env.ref(ZPL_REPORT).id,
            }
        )
        product = product or self.product
        return self.env["stock.picking.line.print"].create(
            dict(
                {
                    "product_id": product.id,
                    "quantity": 1.0,
                    "label_qty": 1,
                    "uom_id": product.uom_id.id,
                    "lot_id": lot.id if lot else False,
                    "location_id": self.location.id,
                    "wizard_id": wizard.id,
                },
                **values
            )
        )

    def _render(self, lines):
        content, _content_type = self.env["ir.actions.report"]._render_qweb_text(
            self.env.ref(ZPL_REPORT), lines.ids
        )
        return content

    def test_one_zpl_block_per_label_copy(self):
        """A roll printer takes a flat stream, so label_qty is the block count."""
        line = self._create_line(lot=self.lot, label_qty=3)
        zpl = self._render(line).decode("cp932")
        self.assertEqual(zpl.count("^XA"), 3)
        self.assertEqual(zpl.count("^XZ"), 3)

    def test_label_carries_every_field_of_the_sheet_label(self):
        line = self._create_line(lot=self.lot)
        zpl = self._render(line).decode("cp932")
        self.assertIn(self.product.default_code, zpl)
        self.assertIn(self.product.name, zpl)
        self.assertIn(self.purchase.name, zpl)
        self.assertIn(self.analytic_account.name, zpl)
        self.assertIn(self.lot.name, zpl)
        self.assertIn("Workshop/SDG-PS1-C14-手前", zpl)

    def test_payload_is_the_one_the_sheet_prints(self):
        """The ZPL is a second output for the same code, not a second code."""
        line = self._create_line(lot=self.lot)
        zpl = self._render(line).decode("cp932")
        self.assertEqual(
            line.gs1_qr_value, "240%s#10%s" % (self.product.default_code, self.lot.name)
        )
        self.assertIn("^BQN,2,3^FDMA,%s^FS" % line.gs1_qr_value, zpl)

    def test_stream_reaches_the_printer_as_cp932(self):
        """^CI15 selects Shift-JIS on the printer, so UTF-8 would be mojibake."""
        line = self._create_line(lot=self.lot)
        content = self._render(line)
        self.assertIn("手前".encode("cp932"), content)
        self.assertNotIn("手前".encode("utf-8"), content)
        self.assertIn(b"\r\n", content)

    def test_a_caret_in_free_text_never_reaches_the_field_data(self):
        """ZPL reads ^ as a command introducer even inside ^FD."""
        # Created rather than copied from the fixture: product.product.copy()
        # duplicates the template and does not carry these values onto the new
        # variant, which would leave the test asserting against the original.
        product = self.env["product.product"].create(
            {
                "name": "Bracket ^FS injected",
                "type": "product",
                "default_code": "CARET-0001",
            }
        )
        line = self._create_line(product=product)
        zpl = self._render(line).decode("cp932")
        self.assertIn("Bracket  FS injected", zpl)
        self.assertNotIn("Bracket ^FS injected", zpl)

    def test_print_refuses_a_line_that_cannot_be_encoded(self):
        """Selecting the ZPL report must refuse exactly what the sheet refuses."""
        product = self.env["product.product"].create(
            {"name": "Product Without A Reference", "type": "product"}
        )
        line = self._create_line(product=product)
        self.assertTrue(line.gs1_qr_error)
        with self.assertRaises(UserError):
            line.wizard_id.print_labels()

    def test_print_allows_a_line_that_can_be_encoded(self):
        """Guards the test above: it would pass on a wizard that never prints."""
        line = self._create_line(lot=self.lot)
        self.assertFalse(line.gs1_qr_error)
        self.assertTrue(line.wizard_id.print_labels())
