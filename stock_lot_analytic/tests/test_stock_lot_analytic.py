# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestStockLotAnalytic(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "tracking": "lot",
            }
        )
        cls.analytic_account = cls.env.ref("analytic.analytic_agrolait")
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.po = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_qty": 2.0,
                            "product_uom": cls.product.uom_id.id,
                            "price_unit": 10.0,
                            "analytic_distribution": {
                                str(cls.analytic_account.id): 100.0
                            },
                        }
                    )
                ],
            }
        )

    def test_stock_lot_analytic_with_incoming_picking(self):
        self.po.button_confirm()
        picking = self.po.picking_ids
        self.assertTrue(picking, "No incoming picking was created.")
        picking.action_assign()
        for ml in picking.move_line_ids:
            ml.lot_name = "test lot"
            ml.qty_done = ml.reserved_uom_qty
        picking._action_done()
        lot = self.env["stock.lot"].search(
            [("product_id", "=", self.product.id), ("name", "=", "test lot")]
        )
        self.assertEqual(
            lot.analytic_distribution,
            self.po.order_line.analytic_distribution,
            "The analytic_distribution on the lot does not match the purchase order line.",
        )
