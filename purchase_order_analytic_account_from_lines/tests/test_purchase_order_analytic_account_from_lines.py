# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


# Purchase orders cannot be created at install, as the fields the modules
# depending on purchase make mandatory are not in the registry yet.
@tagged("post_install", "-at_install")
class TestPurchaseOrderAnalyticAccountFromLines(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        plan_model = cls.env["account.analytic.plan"]
        cls.plan = plan_model.create({"name": "Department"})
        cls.other_plan = plan_model.create({"name": "Project"})
        cls.account, cls.account_2, cls.other_account = cls.env[
            "account.analytic.account"
        ].create(
            [
                {"name": "Department 1", "plan_id": cls.plan.id},
                {"name": "Department 2", "plan_id": cls.plan.id},
                {"name": "Project 1", "plan_id": cls.other_plan.id},
            ]
        )
        cls.partner = cls.env["res.partner"].create({"name": "Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Product", "type": "consu"}
        )
        cls.order = cls.env["purchase.order"].create({"partner_id": cls.partner.id})

    def _line_values(self, distribution=None):
        return {
            "order_id": self.order.id,
            "product_id": self.product.id,
            "product_qty": 1.0,
            "price_unit": 100.0,
            "analytic_distribution": distribution,
        }

    def test_analytic_accounts_of_the_order(self):
        """The order holds the accounts of every one of its lines."""
        line, other_line = self.env["purchase.order.line"].create(
            [
                self._line_values(
                    {str(self.account.id): 50.0, str(self.other_account.id): 50.0}
                ),
                self._line_values({str(self.account_2.id): 100.0}),
            ]
        )
        self.assertEqual(
            self.order.line_analytic_account_ids,
            self.account | self.account_2 | self.other_account,
        )
        # The accounts follow the distribution of the lines, whichever plan
        # they belong to.
        other_line.analytic_distribution = {str(self.other_account.id): 100.0}
        self.assertEqual(
            self.order.line_analytic_account_ids, self.account | self.other_account
        )
        # A deleted account leaves the order, as the distribution it stays
        # behind in holds no reference to it.
        self.other_account.unlink()
        self.assertEqual(self.order.line_analytic_account_ids, self.account)
        # A line without distribution adds none, and an order without lines
        # holds none.
        line.analytic_distribution = False
        self.assertFalse(self.order.line_analytic_account_ids)
        other_line.unlink()
        self.assertFalse(self.order.line_analytic_account_ids)

    def test_archived_account_stays_on_the_order(self):
        """An archived account is kept, so it is back as soon as it is too."""
        self.env["purchase.order.line"].create(
            self._line_values(
                {str(self.account.id): 50.0, str(self.other_account.id): 50.0}
            )
        )
        self.other_account.action_archive()
        # Read with active_test disabled, as whether an archived record is
        # filtered out of an x2many when it is read is up to the ORM. What is
        # tested here is the value the order keeps.
        self.assertEqual(
            self.order.with_context(active_test=False).line_analytic_account_ids,
            self.account | self.other_account,
        )
        self.other_account.action_unarchive()
        self.assertEqual(
            self.order.line_analytic_account_ids, self.account | self.other_account
        )
