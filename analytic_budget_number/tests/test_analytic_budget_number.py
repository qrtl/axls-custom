# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger

ATTRIBUTE_MODELS = [
    "analytic.budget.satellite",
    "analytic.budget.subsystem",
    "analytic.budget.component",
    "analytic.budget.model",
]


# A company cannot be created at install, as the fields the modules loaded
# after this one make mandatory are not in the registry yet.
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
        cls.other_plan = plan_model.create({"name": "Project"})
        cls.plan_b = plan_model.create(
            {"name": "Alt Budget", "is_budget": True, "company_id": cls.company_b.id}
        )

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

    def test_budget_account_follows_the_root_plan(self):
        """is_budget_account is what the form view reads to show the
        attributes on the accounts of the budget plan only, and it is driven by
        the root plan, not by the plan of the account. So an account sitting on
        a subplan of the budget plan is a budget account as well, the way the
        analytic distribution resolves those accounts too.
        """
        account_model = self.env["account.analytic.account"]
        subplan = self.env["account.analytic.plan"].create(
            {"name": "Budget Sub", "parent_id": self.plan.id}
        )
        for name, plan, expected in [
            ("On the budget plan", self.plan, True),
            ("On a subplan of it", subplan, True),
            ("On another plan", self.other_plan, False),
        ]:
            account = account_model.create({"name": name, "plan_id": plan.id})
            self.assertEqual(account.is_budget_account, expected, name)

    def test_attribute_names_are_unique(self):
        """Two values of the same name could not be told apart on an account."""
        for model in ATTRIBUTE_MODELS:
            attribute_model = self.env[model]
            attribute_model.create({"name": "Duplicate"})
            with self.assertRaises(IntegrityError, msg=model), mute_logger(
                "odoo.sql_db"
            ), self.env.cr.savepoint():
                attribute_model.create({"name": "Duplicate"})

    def test_attributes_are_maintained_by_the_analytic_users(self):
        """Whoever maintains the analytic accounts maintains their attributes.

        The values are read by every user, though, as they show on the
        analytic account itself.
        """
        reader = new_test_user(
            self.env, login="budget_attribute_reader", groups="base.group_user"
        )
        writer = new_test_user(
            self.env,
            login="budget_attribute_writer",
            groups="base.group_user,analytic.group_analytic_accounting",
        )
        for model in ATTRIBUTE_MODELS:
            attribute = self.env[model].with_user(writer).create({"name": "Attribute"})
            attribute.name = "Renamed"
            self.assertEqual(attribute.with_user(reader).name, "Renamed", model)
            with self.assertRaises(AccessError, msg=model):
                self.env[model].with_user(reader).create({"name": "Refused"})
            with self.assertRaises(AccessError, msg=model):
                attribute.with_user(reader).name = "Refused"
            attribute.unlink()
