from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductPlm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].set_param(
            "product_lot_sequence.policy", "product"
        )
        cls.item_type = cls.env["plm.item.type"].create({"name": "Test PCBA"})
        cls.mapping = cls.env["plm.product.mapping"].create(
            {
                "item_type_id": cls.item_type.id,
                "product_type": "product",
                "product_categ_id": cls.env.ref("product.product_category_all").id,
                "tracking": "serial",
                "auto_create_lot": True,
            }
        )
        cls.plm_rec = cls.env["product.plm"].create(
            {
                "part_number": "TEST-001",
                "name": "Test Product",
                "mapping_id": cls.mapping.id,
                "company_id": cls.env.company.id,
                "esc_code": "ESC123",
            }
        )

    def test_lot_sequence_prefix_valid(self):
        self.mapping.write({"lot_sequence_prefix": "{esc_code}"})
        self.mapping.write({"lot_sequence_prefix": "STATIC"})
        self.mapping.write({"lot_sequence_prefix": False})
        with self.assertRaises(ValidationError):
            self.mapping.write({"lot_sequence_prefix": "{invalid_key}"})
        with self.assertRaises(ValidationError):
            self.mapping.write({"lot_sequence_prefix": "{"})

    def test_create_products_prefix_from_esc_code(self):
        """create_products() sets lot sequence prefix from ESC ID."""
        self.mapping.write({"lot_sequence_prefix": "{esc_code}"})
        self.env["product.plm"].create_products()
        self.assertEqual(self.plm_rec.state, "done")
        self.assertEqual(self.plm_rec.product_id.lot_sequence_id.prefix, "ESC123")

    def test_create_products_no_prefix_without_esc_code(self):
        """create_products() skips prefix when ESC ID is absent."""
        self.mapping.write({"lot_sequence_prefix": "{esc_code}"})
        self.plm_rec.write({"esc_code": False})
        self.env["product.plm"].create_products()
        self.assertEqual(self.plm_rec.state, "done")
        self.assertFalse(self.plm_rec.product_id.lot_sequence_id.prefix)
