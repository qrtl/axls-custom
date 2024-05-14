# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
from datetime import timedelta

from odoo.tests.common import Form, TransactionCase


class TestProductLastPurchaseDate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestProductLastPurchaseDate, cls).setUpClass()
        cls.product_template = cls.env["product.template"].create(
            {"name": "Test Product", "type": "product"}
        )
        cls.product = cls.product_template.product_variant_ids
        cls.location = cls.env.ref("stock.stock_location_suppliers")
        cls.location_dest = cls.env.ref("stock.stock_location_stock")

    def create_incoming_receipt(self):
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.location.id,
                "location_dest_id": self.location_dest.id,
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Move",
                            "location_id": self.location.id,
                            "location_dest_id": self.location_dest.id,
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        immediate_wizard = picking.button_validate()
        self.assertEqual(immediate_wizard.get("res_model"), "stock.immediate.transfer")
        immediate_wizard_form = Form(
            self.env[immediate_wizard["res_model"]].with_context(
                **immediate_wizard["context"]
            )
        ).save()
        immediate_wizard_form.process()

    def test_product_dates_initially_false(self):
        """Check initial date fields are False."""
        self.assertFalse(self.product_template.last_purchase_date)
        self.assertFalse(self.product_template.man_last_purchase_date)
        self.assertFalse(self.product.last_purchase_date)
        self.assertFalse(self.product.man_last_purchase_date)

    def test_assign_dates_to_variant(self):
        """Assign dates to the variant and check propagation to the template."""
        date = datetime.date.today() + timedelta(days=1)
        self.product.write(
            {
                "last_purchase_date": date,
                "man_last_purchase_date": date,
            }
        )
        self.assertEqual(self.product_template.last_purchase_date, date)
        self.assertEqual(self.product_template.man_last_purchase_date, date)

    def test_receipt_updates_dates(self):
        """Create incoming receipt and check dates update."""
        current_date = datetime.date.today()
        self.create_incoming_receipt()
        self.assertEqual(self.product.last_purchase_date, current_date)
        self.assertEqual(self.product_template.last_purchase_date, current_date)

        # Ensure 'man_last_purchase_date' later than 'last_purchase_date' updates fields.
        date = datetime.date.today() + timedelta(days=3)
        self.product.man_last_purchase_date = date
        self.assertEqual(self.product.last_purchase_date, date)
        self.assertEqual(self.product.man_last_purchase_date, date)
        self.assertEqual(self.product_template.last_purchase_date, date)
        self.assertEqual(self.product_template.man_last_purchase_date, date)

        # Create picking with current date and check dates do not revert
        self.create_incoming_receipt()
        self.assertNotEqual(self.product.last_purchase_date, current_date)
        self.assertNotEqual(self.product_template.last_purchase_date, current_date)
