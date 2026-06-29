# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import new_test_user, tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestStockLocationReportManagerLayout(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.standard_view = cls.env.ref("stock.view_stock_quant_tree")
        cls.editable_view = cls.env.ref("stock.view_stock_quant_tree_editable")
        cls.readonly_view = cls.env.ref(
            "stock_location_report_manager_layout."
            "view_stock_quant_tree_readonly_manager_layout"
        )
        cls.user_plain = new_test_user(
            cls.env, "srml_plain_user", groups="stock.group_stock_user"
        )
        cls.user_manager = new_test_user(
            cls.env, "srml_manager", groups="stock.group_stock_manager"
        )

    def _list_view_id(self, user, **ctx):
        action = (
            self.env["stock.quant"]
            .with_user(user)
            .with_context(**ctx)
            ._get_quants_action()
        )
        return action["view_id"]

    def test_non_manager_gets_readonly_manager_layout(self):
        self.assertEqual(self._list_view_id(self.user_plain), self.readonly_view.id)

    def test_manager_is_unaffected(self):
        # Manager keeps the standard report view, and gets the editable layout in
        # inventory mode -- never the read-only manager layout.
        self.assertEqual(self._list_view_id(self.user_manager), self.standard_view.id)
        self.assertEqual(
            self._list_view_id(self.user_manager, inventory_mode=True),
            self.editable_view.id,
        )
