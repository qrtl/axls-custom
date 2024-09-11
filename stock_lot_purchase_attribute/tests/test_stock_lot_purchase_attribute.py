# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestStockLotPurchaseAttribute(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product = cls.env["product.product"].create(
            {
                "name": "Test Product Tracked by Lot",
                "type": "product",
                "tracking": "lot",
            }
        )
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": 10,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

    def test_stock_lot_purchase_attribute(self):
        # Confirm the purchase order
        self.purchase_order.button_confirm()
        self.assertEqual(self.purchase_order.state, "purchase", "PO not confirmed")

        picking = self.purchase_order.picking_ids
        self.assertTrue(picking, "No incoming picking found.")

        picking.action_confirm()
        picking.action_assign()
        move_line = picking.move_line_ids
        move_line.lot_name = "TestLot"
        move_line.qty_done = 10.0
        picking.button_validate()
        lot = self.env["stock.lot"].search([("name", "=", "TestLot")])
        self.assertEqual(lot.purchase_id, self.purchase_order)
        self.assertEqual(lot.purchase_partner_id, self.vendor)
