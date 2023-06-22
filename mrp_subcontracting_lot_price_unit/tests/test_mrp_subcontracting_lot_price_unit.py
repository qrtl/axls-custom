# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.stock_lot_price_unit.tests.test_stock_lot_price_unit import (
    TestStockLotPriceUnit,
)


class MrpSubcontractingLotPriceUnit(TestStockLotPriceUnit):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.productB.tracking = "lot"
        cls.lot1 = cls.env["stock.lot"].create(
            {
                "product_id": cls.productB.id,
                "company_id": cls.env.user.company_id.id,
                "name": "LOT001",
                "price_unit": 50.00,
            }
        )

    def test_mrp_subcontracting_lot_price_unit(self):
        picking = self.create_picking()
        move = self.create_stock_move(picking, self.productB, 1000)
        self.create_stock_move_line(move, self.lot1)

        picking.action_confirm()
        picking.action_assign()

        move.is_subcontract = True
        picking._action_done()
        # Check if the lot's price_unit is not changed
        self.assertEqual(self.lot1.price_unit, 50.0)
        self.lot.price_unit = 00.0
