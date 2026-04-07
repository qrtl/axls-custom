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
        cls.analytic_plan = cls.env["account.analytic.plan"].create(
            {
                "name": "Test Plan",
                "default_applicability": "optional",
                "company_id": False,
            }
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "Test Analytic Account",
                "plan_id": cls.analytic_plan.id,
            }
        )
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
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "inventory lot",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
                "analytic_distribution": {str(cls.analytic_account.id): 100.0},
            }
        )
        cls.quant = cls.env["stock.quant"].create(
            {
                "location_id": cls.stock_location.id,
                "product_id": cls.product.id,
                "lot_id": cls.lot.id,
                "inventory_quantity": 1.0,
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

    def test_inventory_adjustment_copies_lot_analytic_distribution(self):
        self.quant.action_apply_inventory()
        move = self.env["stock.move"].search(
            [("is_inventory", "=", True), ("move_line_ids.lot_id", "=", self.lot.id)],
            order="id desc",
            limit=1,
        )
        self.assertEqual(
            self.analytic_account.id,
            int(list(self.lot.analytic_distribution.keys())[0]),
            "The analytic_account on the lot does not match the expected value.",
        )
        self.assertEqual(
            move.move_line_ids.analytic_distribution,
            self.lot.analytic_distribution,
            "The analytic_distribution on the inventory move line does not match the lot.",
        )
