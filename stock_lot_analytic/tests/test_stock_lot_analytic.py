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
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.receipt = cls.env["stock.picking"].create(
            {
                "location_id": cls.supplier_location.id,
                "location_dest_id": cls.stock_location.id,
                "partner_id": cls.vendor.id,
                "picking_type_id": cls.env.ref("stock.picking_type_in").id,
                "move_ids": [
                    Command.create(
                        {
                            "name": "Test Move",
                            "location_id": cls.supplier_location.id,
                            "location_dest_id": cls.stock_location.id,
                            "product_id": cls.product.id,
                            "product_uom_qty": 10.0,
                            "price_unit": 10,
                            "analytic_distribution": {
                                str(cls.analytic_account.id): 100.0
                            },
                        }
                    )
                ],
            }
        )

    def test_stock_lot_analytic_with_incoming_picking(self):
        self.receipt.action_assign()
        for ml in self.receipt.move_line_ids:
            ml.lot_name = "test lot"
            ml.qty_done = ml.reserved_uom_qty
        self.receipt._action_done()
        lot = self.env["stock.lot"].search(
            [("product_id", "=", self.product.id), ("name", "=", "test lot")]
        )
        self.assertEqual(
            lot.analytic_distribution,
            self.receipt.move_ids.analytic_distribution,
            "The analytic_distribution on the lot does not match the purchase order line.",
        )
