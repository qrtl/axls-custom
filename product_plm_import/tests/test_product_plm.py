# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from base64 import b64encode

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductPlm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].set_param(
            "product_lot_sequence.policy", "product"
        )
        cls.item_type = cls.env["plm.item.type"].create({"name": "Test Type"})
        cls.categ_a = cls.env["plm.category"].create({"name": "Categ A"})
        cls.categ_b = cls.env["plm.category"].create({"name": "Categ B"})
        cls.categ_wildcard = cls.env["plm.category"].create({"name": "Categ*"})
        cls.buy = cls.env["plm.procure.flag"].create({"name": "Buy"})
        cls.make = cls.env["plm.procure.flag"].create({"name": "Make"})
        cls.lot_item_type = cls.env["plm.item.type"].create({"name": "Test PCBA"})
        cls.lot_mapping = cls.env["plm.product.mapping"].create(
            {
                "item_type_id": cls.lot_item_type.id,
                "product_type": "product",
                "product_categ_id": cls.env.ref("product.product_category_all").id,
                "tracking": "serial",
                "auto_create_lot": True,
            }
        )
        cls.lot_plm = cls.env["product.plm"].create(
            {
                "part_number": "TEST-001",
                "name": "Test Product",
                "mapping_id": cls.lot_mapping.id,
                "company_id": cls.env.company.id,
                "esc_code": "ESC123",
            }
        )

    def _create_mapping(
        self, categories=None, procure_flags=None, product_type="consu"
    ):
        categories = categories or self.env["plm.category"]
        procure_flags = procure_flags or self.env["plm.procure.flag"]
        return self.env["plm.product.mapping"].create(
            {
                "item_type_id": self.item_type.id,
                "category_ids": [Command.set(categories.ids)],
                "procure_flag_ids": [Command.set(procure_flags.ids)],
                "product_type": product_type,
                "product_categ_id": self.env.ref("product.product_category_all").id,
            }
        )

    def _create_plm(self):
        return self.env["product.plm"].create(
            {
                "item_type": "Test Type",
                "category": "Categ A",
                "procure_flag": "Buy",
                "company_id": self.env.company.id,
            }
        )

    def test_tie_fails_the_record(self):
        self._create_mapping(
            categories=self.categ_a | self.categ_b,
            procure_flags=self.buy,
            product_type="product",
        )
        self._create_mapping(categories=self.categ_a, procure_flags=self.buy)
        self.env["product.product"].create({"name": "Part", "default_code": "P-1"})
        csv = (
            "Part Number,Name,ESC ID,Procure flag,Item Type,Category,"
            "Unit of Material,Acceptance Test Category,Description,Spec,"
            "Drawing No,Generic Name\n"
            "P-1,Part,,Buy,Test Type,Categ A,,,Part,,,\n"
        )
        wizard = self.env["product.plm.import"].create(
            {"import_file": b64encode(csv.encode()), "file_name": "plm.csv"}
        )
        wizard.import_product_plm()
        plm = self.env["product.plm"].search([("part_number", "=", "P-1")])
        self.assertFalse(plm.mapping_id)
        self.assertEqual(plm.state, "failed")
        self.assertIn("There is already a product for P-1.", plm.error_message)
        self.assertIn(
            "Multiple PLM-product mappings match equally: "
            "Test Type / Categ A, Categ B / Buy; Test Type / Categ A / Buy",
            plm.error_message,
        )

    def test_mismatch_drops_mapping(self):
        plm = self._create_plm()
        self._create_mapping(categories=self.categ_b)
        self._create_mapping(procure_flags=self.make)
        # Used to be -1 + 1 = 0, a tie with the mapping without keys
        self._create_mapping(categories=self.categ_b, procure_flags=self.buy)
        self._create_mapping(categories=self.categ_a, procure_flags=self.make)
        plm._assign_mapping()
        self.assertFalse(plm.mapping_id)
        self.assertEqual(plm.state, "failed")
        self.assertEqual(plm.error_message, "No PLM-product mapping record found.")
        default = self._create_mapping()
        plm._assign_mapping()
        self.assertEqual(plm.mapping_id, default)

    def test_higher_rank_wins(self):
        plm = self._create_plm()
        # Added from rank 6 up to rank 1, each mapping beats the ones before it
        for categories, procure_flags, score in [
            (None, None, 0.0),
            (None, self.buy, 0.5),
            (self.categ_wildcard, None, 0.75),
            (self.categ_a, None, 1.0),
            (self.categ_wildcard, self.buy, 1.25),
            (self.categ_a, self.buy, 1.5),
        ]:
            with self.subTest(score=score):
                mapping = self._create_mapping(categories, procure_flags)
                self.assertEqual(mapping._get_score(plm), score)
                self.assertEqual(plm._get_plm_product_mapping(), mapping)

    def test_lot_sequence_prefix_valid(self):
        self.lot_mapping.write({"lot_sequence_prefix": "{esc_code}"})
        self.lot_mapping.write({"lot_sequence_prefix": "STATIC"})
        self.lot_mapping.write({"lot_sequence_prefix": False})
        with self.assertRaises(ValidationError):
            self.lot_mapping.write({"lot_sequence_prefix": "{invalid_key}"})
        with self.assertRaises(ValidationError):
            self.lot_mapping.write({"lot_sequence_prefix": "{"})

    def test_create_products_prefix_from_esc_code(self):
        """create_products() sets lot sequence prefix from ESC ID."""
        self.lot_mapping.write({"lot_sequence_prefix": "{esc_code}"})
        self.env["product.plm"].create_products()
        self.assertEqual(self.lot_plm.state, "done")
        self.assertEqual(self.lot_plm.product_id.lot_sequence_id.prefix, "ESC123")

    def test_create_products_no_prefix_without_esc_code(self):
        """create_products() skips prefix when ESC ID is absent."""
        self.lot_mapping.write({"lot_sequence_prefix": "{esc_code}"})
        self.lot_plm.write({"esc_code": False})
        self.env["product.plm"].create_products()
        self.assertEqual(self.lot_plm.state, "done")
        self.assertFalse(self.lot_plm.product_id.lot_sequence_id.prefix)
