# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged


# Purchase orders cannot be created at install, as the fields the modules
# depending on purchase make mandatory are not in the registry yet.
@tagged("post_install", "-at_install")
class TestAnalyticBudgetNumber(TransactionCase):
    """The _b fixtures below belong to the second company, the others to the
    current one, which every default falls back to."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        plan_model = cls.env["account.analytic.plan"]
        cls.company = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Other Company"})
        cls.env.user.company_ids |= cls.company_b
        cls.plan = plan_model.create({"name": "Budget", "is_budget": True})
        cls.subplan = plan_model.create({"name": "FY26", "parent_id": cls.plan.id})
        cls.other_plan = plan_model.create({"name": "Project"})
        cls.other_subplan = plan_model.create(
            {"name": "Phase 1", "parent_id": cls.other_plan.id}
        )
        # The name sorts before the one of the plan of the current company, so
        # that a plan taken without regard for the company would be this one.
        cls.plan_b = plan_model.create(
            {"name": "Alt Budget", "is_budget": True, "company_id": cls.company_b.id}
        )
        # The accounts default to the current company as the plans do, which
        # keeps them company consistent. They are created in one batch, so that
        # cls.account is the oldest account of the budget plan.
        (
            cls.account,
            cls.account_2,
            cls.subplan_account,
            cls.other_account,
            cls.other_subplan_account,
            cls.account_b,
        ) = cls.env["account.analytic.account"].create(
            [
                {"name": "Budget 1", "plan_id": cls.plan.id},
                {"name": "Budget 2", "plan_id": cls.plan.id},
                {"name": "Budget FY26", "plan_id": cls.subplan.id},
                {"name": "Project 1", "plan_id": cls.other_plan.id},
                {"name": "Project Phase 1", "plan_id": cls.other_subplan.id},
                {
                    "name": "Alt Budget 1",
                    "plan_id": cls.plan_b.id,
                    "company_id": cls.company_b.id,
                },
            ]
        )
        cls.partner = cls.env["res.partner"].create({"name": "Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Product", "type": "consu"}
        )
        cls.order = cls.env["purchase.order"].create({"partner_id": cls.partner.id})
        cls.order_b = (
            cls.env["purchase.order"]
            .with_company(cls.company_b)
            .create({"partner_id": cls.partner.id, "company_id": cls.company_b.id})
        )

    def _line_values(self, distribution=None, order=None):
        return {
            "order_id": (order or self.order).id,
            "product_id": self.product.id,
            "product_qty": 1.0,
            "price_unit": 100.0,
            "analytic_distribution": distribution,
        }

    def _create_line(self, distribution=None, order=None):
        return self.env["purchase.order.line"].create(
            self._line_values(distribution, order)
        )

    def test_budget_number_follows_the_distribution(self):
        """Each line is kept in step with the budget accounts it is distributed to."""
        line, subplan_line, plain_line = self.env["purchase.order.line"].create(
            [
                self._line_values({str(self.account.id): 100.0}),
                self._line_values({str(self.subplan_account.id): 100.0}),
                self._line_values(),
            ]
        )
        self.assertEqual(line.analytic_budget_id, self.account)
        # The accounts of the subplans of the budget plan are budget numbers.
        self.assertEqual(subplan_line.analytic_budget_id, self.subplan_account)
        self.assertFalse(plain_line.analytic_budget_id)
        # Writing on a stored line is the only thing that recomputes the field
        # in production, so it is what the depends has to cover.
        plain_line.analytic_distribution = {
            str(self.other_account.id): 40.0,
            str(self.account.id): 60.0,
        }
        self.assertEqual(plain_line.analytic_budget_id, self.account)
        # The accounts of another plan and of its subplans stay out.
        plain_line.analytic_distribution = {
            str(self.other_account.id): 50.0,
            str(self.other_subplan_account.id): 50.0,
        }
        self.assertFalse(plain_line.analytic_budget_id)
        # Among the accounts of the budget plan the oldest wins, whatever its
        # share, and jsonb reorders the keys, so it has to win once the
        # distribution is no longer the dict it was written as.
        line.analytic_distribution = {
            str(self.account_2.id): 62.5,
            str(self.account.id): 37.5,
        }
        self.assertEqual(line.analytic_budget_id, self.account)
        line.flush_recordset()
        line.invalidate_recordset()
        line.modified(["analytic_distribution"])
        self.assertEqual(line.analytic_budget_id, self.account)

    def test_budget_number_when_its_account_goes_away(self):
        """Archiving keeps the budget number, deleting falls back to the next."""
        distribution = {str(self.account.id): 37.5, str(self.account_2.id): 62.5}
        line = self._create_line(distribution)
        self.account.active = False
        line.modified(["analytic_distribution"])
        self.assertEqual(line.analytic_budget_id, self.account)
        # No manual recompute here: the unlink of the account is what has to
        # trigger it, as the distribution keeps the key of the deleted account
        # and the foreign key of the budget number is set null on delete.
        self.account.unlink()
        self.assertEqual(line.analytic_budget_id, self.account_2)
        self.assertEqual(line.analytic_distribution, distribution)
        # With no other budget account left the budget number is cleared.
        self.account_2.unlink()
        self.assertFalse(line.analytic_budget_id)

    def test_budget_plan_is_resolved_per_company(self):
        """Each line resolves the budget plan flagged for its own company."""
        line = self._create_line({str(self.account.id): 100.0})
        line_b = self._create_line({str(self.account_b.id): 100.0}, order=self.order_b)
        # The budget plan of a company is no budget plan for the other ones.
        cross_line = self._create_line({str(self.account_b.id): 100.0})
        self.assertEqual(line.analytic_budget_id, self.account)
        self.assertEqual(line_b.analytic_budget_id, self.account_b)
        self.assertFalse(cross_line.analytic_budget_id)
        # The company of the line is what picks the plan, so moving the order
        # over switches the budget number of its lines.
        line.analytic_distribution = {
            str(self.account.id): 50.0,
            str(self.account_b.id): 50.0,
        }
        self.order.company_id = self.company_b
        self.assertEqual(line.company_id, self.company_b)
        self.assertEqual(line.analytic_budget_id, self.account_b)
        # A company without a budget plan takes none, even though the line is
        # still distributed to a budget account of the other company.
        self.plan_b.is_budget = False
        line.modified(["analytic_distribution"])
        self.assertFalse(line.analytic_budget_id)

    def test_budget_plan_shared_by_every_company(self):
        """The account taken is of the company of the line, or of no company."""
        # A plan of a single company cannot hold an account of no company, so a
        # shared plan is what it takes for an account of no company to compete
        # with one of another company. The account of no company is the oldest.
        (self.plan | self.plan_b).is_budget = False
        shared_plan = self.env["account.analytic.plan"].create(
            {"name": "Shared Budget", "is_budget": True, "company_id": False}
        )
        any_account, account, account_b = self.env["account.analytic.account"].create(
            [
                {"name": "Shared Any", "plan_id": shared_plan.id, "company_id": False},
                {"name": "Shared 1", "plan_id": shared_plan.id},
                {
                    "name": "Shared 2",
                    "plan_id": shared_plan.id,
                    "company_id": self.company_b.id,
                },
            ]
        )
        line = self._create_line({str(account.id): 100.0})
        # The account of the other company is no budget number here, even
        # though its plan is the budget plan of every company.
        cross_line = self._create_line({str(account_b.id): 100.0})
        self.assertEqual(line.analytic_budget_id, account)
        self.assertFalse(cross_line.analytic_budget_id)
        # The account of no company is a budget number for every company, and
        # the oldest of the three, so it wins the tiebreak on both companies.
        both_line = self._create_line(
            {str(any_account.id): 50.0, str(account.id): 50.0}
        )
        both_line_b = self._create_line(
            {str(any_account.id): 50.0, str(account_b.id): 50.0}, order=self.order_b
        )
        self.assertEqual(both_line.analytic_budget_id, any_account)
        self.assertEqual(both_line_b.analytic_budget_id, any_account)
        # Deleting it has to fix the lines of every company, including the ones
        # the record rules hide from the user: unlink collects them as
        # superuser, and compute_sudo recomputes them as superuser. Without
        # either the budget number would be lost instead of falling back.
        user = new_test_user(
            self.env,
            login="budget_line_user",
            groups="base.group_user,purchase.group_purchase_user,"
            "analytic.group_analytic_accounting",
            company_id=self.company.id,
        )
        user_env = self.env(user=user)
        self.assertFalse(
            user_env["purchase.order.line"].search([("id", "=", both_line_b.id)])
        )
        self.assertFalse(
            user_env["account.analytic.account"].search([("id", "=", account_b.id)])
        )
        any_account.with_user(user).unlink()
        # The recompute the unlink asks for stays pending until the environment
        # of the user is flushed, and that is the one it then runs in.
        user_env.flush_all()
        self.assertEqual(both_line.analytic_budget_id, account)
        self.assertEqual(both_line_b.analytic_budget_id, account_b)

    def test_only_one_budget_plan_per_company(self):
        """A company has one budget plan at most, and the flag can be moved."""
        with self.assertRaises(ValidationError):
            self.other_plan.is_budget = True
        # The remediation the error message points at: disable the plan in
        # place first, then flag the other one.
        self.plan.is_budget = False
        self.other_plan.is_budget = True
        # Only the fields present in the values are validated on create, so
        # creating a flagged plan is a trigger of its own.
        with self.assertRaises(ValidationError):
            self.env["account.analytic.plan"].create(
                {"name": "Budget 2", "is_budget": True}
            )
        # The plan of the other company does not compete with it, until it is
        # shared with every company.
        with self.assertRaises(ValidationError):
            self.plan_b.company_id = False
        # And the other way around: a plan shared by every company blocks the
        # plan of a single one.
        self.other_plan.is_budget = False
        self.plan_b.company_id = False
        with self.assertRaises(ValidationError):
            self.plan.is_budget = True

    def test_conflicting_budget_plan_of_an_unreachable_company_is_found(self):
        """The uniqueness check reaches the budget plan of any company.

        The multi company record rule hides the plan flagged for another company
        from the user, so without sudo a plan shared by every company would be
        let through and leave the database with two budget plans.
        """
        self.plan.is_budget = False
        user = new_test_user(
            self.env,
            login="budget_plan_user",
            groups="base.group_user,analytic.group_analytic_accounting",
            company_id=self.company.id,
        )
        plan = self.other_plan.with_user(user)
        self.assertFalse(plan.search([("is_budget", "=", True)]))
        with self.assertRaises(ValidationError):
            plan.write({"company_id": False, "is_budget": True})

    def test_recompute_action_after_a_configuration_change(self):
        """Configuration changes leave the field stale until the action is run.

        The server action is run here as the Action menu runs it, code string
        included.
        """
        line = self._create_line(
            {str(self.account.id): 50.0, str(self.other_account.id): 50.0}
        )
        # Read the field before moving the flag, so that it is stored against
        # the configuration in place, as a line of the history would be.
        self.assertEqual(line.analytic_budget_id, self.account)
        self.plan.is_budget = False
        self.other_plan.is_budget = True
        # Nothing in the depends can reach a change of the flag, so the stored
        # value stays behind.
        self.assertEqual(line.analytic_budget_id, self.account)
        action = self.env.ref(
            "analytic_budget_number.purchase_order_line_recompute_budget_action"
        )
        selection = action.with_context(
            active_model="purchase.order.line", active_ids=line.ids
        )
        selection.run()
        self.assertEqual(line.analytic_budget_id, self.other_account)
        # Run outside a record selection the action has nothing to recompute,
        # rather than failing on the records it was not given.
        action.run()
        self.assertEqual(line.analytic_budget_id, self.other_account)
        # Without any budget plan no line carries a budget number.
        (self.other_plan | self.plan_b).is_budget = False
        selection.run()
        self.assertFalse(line.analytic_budget_id)
