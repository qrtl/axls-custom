# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.purchase_stock.tests.test_create_picking import TestCreatePicking


class TestStockLotAnalytic(TestCreatePicking):
    def test_stock_lot_analytic_with_incoming_picking(self):
        self.product_id_1.tracking = "lot"
        self.po = self.env["purchase.order"].create(self.po_vals)
        self.po.order_line.write(
            {
                "analytic_distribution": {
                    str(self.env.ref("analytic.analytic_agrolait").id): 100.0
                }
            }
        )
        self.po.button_confirm()
        self.picking = self.po.picking_ids[0]
        for ml in self.picking.move_line_ids:
            ml.lot_name = "test lot"
            ml.qty_done = ml.reserved_uom_qty
        self.picking._action_done()
        lot_analytic = self.env["stock.lot"].search(
            [("product_id", "=", self.product_id_1.id), ("name", "=", "test lot")]
        )
        self.assertEqual(
            lot_analytic.analytic_distribution, self.po.order_line.analytic_distribution
        )
