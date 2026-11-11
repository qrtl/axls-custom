# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged

from odoo.addons.stock_valuation_fifo_lot.tests.common import (
    TestStockValuationFifoCommon,
)

from ..models.stock_valuation_layer import BACKFILL_DONE, BACKFILL_PARAM


@tagged("post_install", "-at_install")
class TestStockValuationLotAllocation(TestStockValuationFifoCommon):
    def _get_lot(self, name):
        return self.env["stock.lot"].search(
            [("product_id", "=", self.product.id), ("name", "=", name)], limit=1
        )

    def _get_allocations(self, layer=None, lot=None):
        domain = [("product_id", "=", self.product.id)]
        if layer:
            domain.append(("valuation_layer_id", "=", layer.id))
        if lot:
            domain.append(("lot_id", "=", lot.id))
        return self.env["stock.valuation.lot.allocation"].search(domain)

    def _get_split(self, layer):
        return {
            allocation.lot_id.name: (
                allocation.allocated_amount,
                allocation.allocated_quantity,
            )
            for allocation in self._get_allocations(layer=layer)
        }

    def _reallocate(self, layers):
        layers.lot_allocation_ids.unlink()
        layers._allocate_to_lots()

    def _get_expense_account(self):
        return self.env["account.account"].search(
            [("account_type", "=", "expense")], limit=1
        )

    def _create_value_only_layer(self, value, move=None, layer=None):
        new_layer = self.env["stock.valuation.layer"].create(
            {
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "description": "Test value-only layer",
                "value": value,
                "unit_cost": 0,
                "quantity": 0,
                "remaining_qty": 0,
                "stock_move_id": move.id if move else False,
                "stock_valuation_layer_id": layer.id if layer else False,
            }
        )
        layer.remaining_value += value
        return new_layer

    def _revalue(self, added_value, lot=None):
        self.env["stock.valuation.layer.revaluation"].create(
            {
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "lot_id": lot.id if lot else False,
                "added_value": added_value,
                "reason": "Test revaluation",
                "account_id": self._get_expense_account().id,
            }
        ).action_validate_revaluation()

    def _assert_invariant(self):
        layers = self.env["stock.valuation.layer"].search(
            [("product_id", "=", self.product.id)]
        )
        for layer in layers.filtered("lot_allocation_ids"):
            allocations = layer.lot_allocation_ids.filtered(
                lambda x: not x.is_opening_adjustment
            )
            self.assertAlmostEqual(
                sum(allocations.mapped("allocated_amount")), layer.value, places=2
            )
        move_lines = self.env["stock.move.line"].search(
            [("product_id", "=", self.product.id)]
        )
        for lot in move_lines.mapped("lot_id"):
            lot_lines = move_lines.filtered(lambda x, lot=lot: x.lot_id == lot)
            allocations = self._get_allocations(lot=lot)
            self.assertAlmostEqual(
                sum(allocations.mapped("allocated_amount")),
                sum(lot_lines.mapped("value_remaining")),
                delta=0.01,
                msg="Allocation mismatch on lot %s" % lot.name,
            )
            self.assertAlmostEqual(
                sum(allocations.mapped("allocated_quantity")),
                sum(lot_lines.mapped("qty_remaining")),
                msg="Quantity mismatch on lot %s" % lot.name,
            )
        self.assertAlmostEqual(
            sum(self._get_allocations().mapped("allocated_amount")),
            sum(move_lines.mapped("value_remaining")),
            places=2,
        )

    def test_receipt(self):
        """Each lot gets its quantity, and the rounded shares add up to the layer."""
        __, move = self.create_picking(
            "in", ["001", "002", "003"], ml_qty=1.0, price=3.335
        )
        layer = move.stock_valuation_layer_ids
        allocations = self._get_allocations(layer=layer)
        self.assertEqual(allocations.mapped("allocated_quantity"), [1.0] * 3)
        self.assertEqual(sum(allocations.mapped("allocated_amount")), layer.value)
        self._assert_invariant()

    def test_receipt_in_other_uom(self):
        """The quantity is in the product UoM, not the move UoM."""
        dozen = self.env.ref("uom.product_uom_dozen")
        pick = self.env["stock.picking"].create(
            {
                "location_id": self.vendor_loc.id,
                "location_dest_id": self.stock_loc.id,
                "picking_type_id": self.pick_type_in.id,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": "Test",
                "product_id": self.product.id,
                "location_id": self.vendor_loc.id,
                "location_dest_id": self.stock_loc.id,
                "product_uom": dozen.id,
                "product_uom_qty": 1.0,
                "picking_id": pick.id,
                "price_unit": 10.0,
            }
        )
        self.env["stock.move.line"].create(
            {
                "move_id": move.id,
                "picking_id": pick.id,
                "product_id": self.product.id,
                "location_id": self.vendor_loc.id,
                "location_dest_id": self.stock_loc.id,
                "product_uom_id": dozen.id,
                "qty_done": 1.0,
                "lot_name": "001",
            }
        )
        pick.action_confirm()
        pick._action_done()
        self.assertEqual(
            self._get_split(move.stock_valuation_layer_ids), {"001": (120.0, 12.0)}
        )
        self._assert_invariant()

    def test_delivery_with_differing_costs(self):
        """Each lot, a zero-cost one included, is charged what FIFO took from it."""
        __, move_in = self.create_picking("in", ["001"], ml_qty=5.0, price=0.0)
        self.create_picking("in", ["002"], ml_qty=5.0, price=12.0)
        __, move_out = self.create_picking("out", ["001", "002"], ml_qty=5.0)
        self.assertEqual(
            self._get_split(move_in.stock_valuation_layer_ids), {"001": (0.0, 5.0)}
        )
        layer = move_out.stock_valuation_layer_ids
        expected = {"001": (0.0, -5.0), "002": (-60.0, -5.0)}
        self.assertEqual(self._get_split(layer), expected)
        self._reallocate(layer)
        self.assertEqual(self._get_split(layer), expected)
        self._assert_invariant()

    def test_delivery_with_force_fifo_lot(self):
        """The lot whose FIFO balance is consumed is charged, not the one shipped."""
        self.create_picking("in", ["001"], ml_qty=5.0, price=10.0)
        self.create_picking("in", ["002"], ml_qty=5.0, price=12.0)
        self.create_picking("out", ["002"], ml_qty=5.0)
        __, move_out = self.create_picking(
            "out", ["002"], ml_qty=5.0, force_lot_name="001"
        )
        self.assertEqual(
            self._get_split(move_out.stock_valuation_layer_ids),
            {"001": (-50.0, -5.0)},
        )
        self._assert_invariant()

    def test_landed_cost_and_price_difference(self):
        """Value-only layers go to what the lots held when they were posted."""
        __, move_in = self.create_picking("in", ["001", "002"], ml_qty=5.0, price=10.0)
        receipt = move_in.stock_valuation_layer_ids
        landed_cost = self._create_value_only_layer(20.0, move=move_in, layer=receipt)
        self.create_picking("out", ["001"], ml_qty=5.0)
        price_difference = self._create_value_only_layer(20.0, layer=receipt)
        expected = {
            landed_cost: {"001": (10.0, 0.0), "002": (10.0, 0.0)},
            price_difference: {"002": (20.0, 0.0)},
        }
        for layer, split in expected.items():
            self.assertEqual(self._get_split(layer), split)
        self._reallocate(landed_cost | price_difference)
        for layer, split in expected.items():
            self.assertEqual(self._get_split(layer), split)
        self._assert_invariant()

    def test_product_revaluation(self):
        """A product revaluation goes to every lot in stock."""
        self.create_picking("in", ["001"], ml_qty=5.0, price=10.0)
        self.create_picking("in", ["002"], ml_qty=15.0, price=10.0)
        self._revalue(100.0)
        layer = self.env["stock.valuation.layer"].search(
            [("product_id", "=", self.product.id), ("quantity", "=", 0)]
        )
        expected = {"001": (25.0, 0.0), "002": (75.0, 0.0)}
        self.assertEqual(self._get_split(layer), expected)
        self.create_picking("out", ["001"], ml_qty=5.0)
        self._reallocate(layer)
        self.assertEqual(self._get_split(layer), expected)
        self._assert_invariant()

    def test_lot_revaluation(self):
        """A revalued lot has no single receipt rate, yet the backfill splits its
        delivery exactly."""
        self.create_picking("in", ["001", "002"], ml_qty=5.0, price=100.0)
        lot = self._get_lot("001")
        self._revalue(50.0, lot=lot)
        self.assertEqual(
            sum(self._get_allocations(lot=lot).mapped("allocated_amount")), 550.0
        )
        __, move_out = self.create_picking("out", ["001", "002"], ml_qty=1.0)
        layer = move_out.stock_valuation_layer_ids
        expected = {"001": (-110.0, -1.0), "002": (-100.0, -1.0)}
        self.assertEqual(self._get_split(layer), expected)
        self._reallocate(layer)
        self.assertEqual(self._get_split(layer), expected)
        self._assert_invariant()

    def test_backfill_cron(self):
        """The cron backfills one batch per run, idles once done, and resumes
        without duplicates when its progress is cleared."""
        __, move_1 = self.create_picking("in", ["001"], ml_qty=5.0, price=10.0)
        __, move_2 = self.create_picking("in", ["002"], ml_qty=5.0, price=20.0)
        layer_1 = move_1.stock_valuation_layer_ids
        layer_2 = move_2.stock_valuation_layer_ids
        self._get_allocations().unlink()
        params = self.env["ir.config_parameter"].sudo()
        params.set_param(BACKFILL_PARAM, False)
        layers = self.env["stock.valuation.layer"]
        layers._cron_backfill_lot_allocations(1)
        self.assertEqual(self._get_split(layer_2), {"002": (100.0, 5.0)})
        self.assertFalse(layer_1.lot_allocation_ids)
        layers._cron_backfill_lot_allocations(2000)
        self.assertEqual(self._get_split(layer_1), {"001": (50.0, 5.0)})
        self.assertEqual(int(params.get_param(BACKFILL_PARAM)), BACKFILL_DONE)
        layer_1.lot_allocation_ids.unlink()
        layers._cron_backfill_lot_allocations(2000)
        self.assertFalse(layer_1.lot_allocation_ids)
        params.set_param(BACKFILL_PARAM, False)
        layers._cron_backfill_lot_allocations(2000)
        self.assertEqual(self._get_split(layer_1), {"001": (50.0, 5.0)})
        self.assertEqual(len(layer_2.lot_allocation_ids), 1)
        self.assertFalse(self._get_allocations().filtered("is_opening_adjustment"))
        self._assert_invariant()

    def test_balancing_pass(self):
        """A per-lot gap left by the backfill lands in one adjustment row per lot."""
        __, move = self.create_picking("in", ["001", "002"], ml_qty=5.0, price=10.0)
        layer = move.stock_valuation_layer_ids
        lot_1, lot_2 = self._get_lot("001"), self._get_lot("002")
        self._get_allocations(layer=layer, lot=lot_1).allocated_amount = 0.0
        self._get_allocations(layer=layer, lot=lot_2).allocated_amount = 100.0
        self.env["stock.valuation.layer"]._balance_lot_allocations()
        for lot, gap in ((lot_1, 50.0), (lot_2, -50.0)):
            adjustment = self._get_allocations(lot=lot).filtered(
                "is_opening_adjustment"
            )
            self.assertEqual(adjustment.allocated_amount, gap)
            self.assertEqual(adjustment.allocated_quantity, 0.0)
        self._assert_invariant()
