# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase


class TestPurchaseOrderNoOwner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.owner = cls.env["res.partner"].create({"name": "Test Owner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "product", "purchase_method": "purchase"}
        )
        cls.order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_qty": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        # The check is skipped during test runs unless it is explicitly requested.
        cls.order = cls.order.with_context(test_purchase_order_no_owner=True)

    def test_01_confirm_without_owner(self):
        with self.assertRaises(UserError):
            self.order.button_confirm()
        self.assertEqual(self.order.state, "draft")

    def test_02_confirm_with_owner(self):
        self.order.owner_id = self.owner
        self.order.button_confirm()
        self.assertEqual(self.order.state, "purchase")

    def test_03_confirm_with_no_owner_flag(self):
        self.order.no_owner = True
        self.order.button_confirm()
        self.assertEqual(self.order.state, "purchase")

    def test_04_check_skipped_without_context(self):
        """Other modules' tests confirming a purchase order are not affected."""
        self.order.with_context(test_purchase_order_no_owner=False).button_confirm()
        self.assertEqual(self.order.state, "purchase")

    def test_05_onchange_no_owner_resets_owner(self):
        with Form(self.order) as order_form:
            order_form.owner_id = self.owner
            order_form.no_owner = True
        self.assertFalse(self.order.owner_id)
