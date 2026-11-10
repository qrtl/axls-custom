# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestPlmProductMapping(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.item_type = cls.env["plm.item.type"].create({"name": "Test Type"})
        cls.categ_a = cls.env["plm.category"].create({"name": "Categ A"})
        cls.categ_b = cls.env["plm.category"].create({"name": "Categ B"})
        cls.categ_wildcard = cls.env["plm.category"].create({"name": "Categ*"})
        cls.buy = cls.env["plm.procure.flag"].create({"name": "Buy"})
        cls.make = cls.env["plm.procure.flag"].create({"name": "Make"})
        cls.plm = cls._create_plm("Categ A", "Buy")

    @classmethod
    def _create_plm(cls, category, procure_flag):
        return cls.env["product.plm"].create(
            {
                "item_type": "Test Type",
                "category": category,
                "procure_flag": procure_flag,
                "company_id": cls.env.company.id,
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

    def test_tie_fails_the_record(self):
        storable = self._create_mapping(
            categories=self.categ_a | self.categ_b, product_type="product"
        )
        consumable = self._create_mapping(procure_flags=self.buy)
        self.assertEqual(self.plm._get_plm_product_mapping(), storable | consumable)
        self.plm._assign_mapping()
        self.assertFalse(self.plm.mapping_id)
        self.assertEqual(self.plm.state, "failed")
        self.assertIn("Test Type / Categ A, Categ B / -", self.plm.error_message)
        self.assertIn("Test Type / - / Buy", self.plm.error_message)

    def test_category_mapping_with_procure_flag_wins(self):
        storable = self._create_mapping(
            categories=self.categ_a | self.categ_b,
            procure_flags=self.buy,
            product_type="product",
        )
        consumable = self._create_mapping(procure_flags=self.buy)
        self.plm._assign_mapping()
        self.assertEqual(self.plm.mapping_id, storable)
        self.assertEqual(self.plm.state, "draft")
        # The category mapping applies to Buy only
        plm_make = self._create_plm("Categ A", "Make")
        self.assertFalse(plm_make._get_plm_product_mapping())
        # The procure flag mapping applies to Buy whatever the category
        plm_other = self._create_plm("Categ C", "Buy")
        self.assertEqual(plm_other._get_plm_product_mapping(), consumable)

    def test_mismatch_drops_mapping(self):
        self._create_mapping(categories=self.categ_b, procure_flags=self.buy)
        default = self._create_mapping()
        # Used to be -1 + 1 = 0, a tie with the mapping without keys
        self.assertEqual(self.plm._get_plm_product_mapping(), default)
        self._create_mapping(categories=self.categ_a, procure_flags=self.make)
        self.assertEqual(self.plm._get_plm_product_mapping(), default)

    def test_mapping_without_keys_applies_to_anything(self):
        default = self._create_mapping()
        self.assertEqual(default._get_score(self.plm), 0.0)
        mismatch = self._create_mapping(categories=self.categ_b)
        self.assertIsNone(mismatch._get_score(self.plm))
        self.plm._assign_mapping()
        self.assertEqual(self.plm.mapping_id, default)

    def test_no_mapping_applies(self):
        self._create_mapping(categories=self.categ_b)
        self._create_mapping(procure_flags=self.make)
        self.plm._assign_mapping()
        self.assertFalse(self.plm.mapping_id)
        self.assertEqual(self.plm.state, "failed")
        self.assertEqual(self.plm.error_message, "No PLM-product mapping record found.")

    def test_wildcard_scores_half(self):
        self._create_mapping(categories=self.categ_a)
        wildcard = self._create_mapping(
            categories=self.categ_wildcard, procure_flags=self.buy
        )
        # 0.5 + 1 against 1 + 0
        self.assertEqual(wildcard._get_score(self.plm), 1.5)
        self.assertEqual(self.plm._get_plm_product_mapping(), wildcard)
        exact = self._create_mapping(categories=self.categ_a, procure_flags=self.buy)
        # 1 + 1 against the two above
        self.assertEqual(self.plm._get_plm_product_mapping(), exact)

    def test_identical_mappings_tie(self):
        first = self._create_mapping(categories=self.categ_a, procure_flags=self.buy)
        second = self._create_mapping(categories=self.categ_a, procure_flags=self.buy)
        self.assertEqual(self.plm._get_plm_product_mapping(), first | second)
        self.plm._assign_mapping()
        self.assertFalse(self.plm.mapping_id)
        self.assertEqual(self.plm.state, "failed")

    def test_result_does_not_depend_on_record_order(self):
        consumable = self._create_mapping(procure_flags=self.buy)
        storable = self._create_mapping(
            categories=self.categ_a, procure_flags=self.buy, product_type="product"
        )
        self.assertEqual(self.plm._get_plm_product_mapping(), storable)
        storable.write({"default_active": True})
        consumable.write({"default_active": True})
        self.assertEqual(self.plm._get_plm_product_mapping(), storable)

    def test_mapping_order_does_not_change_on_save(self):
        first = self._create_mapping()
        second = self._create_mapping()
        first.write({"default_active": True})
        mappings = self.env["plm.product.mapping"].search(
            [("item_type_id", "=", self.item_type.id)]
        )
        self.assertEqual(mappings.ids, [first.id, second.id])
