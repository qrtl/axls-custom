# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import Form, TransactionCase


class TestPurchaseDepositPreserveAmount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "test company",
                "currency_id": cls.env.ref("base.JPY").id,
                "country_id": cls.env.ref("base.jp").id,
            }
        )
        cls.env.user.company_id = cls.company
        cls.currency_usd = cls.env.ref("base.USD")
        cls.currency_usd.active = True
        Rate = cls.env["res.currency.rate"]
        Rate.create(
            {
                "name": "2025-10-01",
                "currency_id": cls.currency_usd.id,
                "company_id": cls.company.id,
                "rate": 1 / 150.0,
            }
        )
        Rate.create(
            {
                "name": "2025-11-01",
                "currency_id": cls.currency_usd.id,
                "company_id": cls.company.id,
                "rate": 1 / 160.0,
            }
        )
        Account = cls.env["account.account"]
        account_payable = Account.create(
            {
                "code": "TEST1",
                "name": "Payable",
                "reconcile": True,
                "account_type": "liability_payable",
                "company_id": cls.company.id,
            }
        )
        account_expense = Account.create(
            {
                "code": "TEST2",
                "name": "Expense",
                "account_type": "expense",
                "company_id": cls.company.id,
            }
        )
        stock_valuation = Account.create(
            {
                "code": "TEST3",
                "name": "Stock Valuation",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        stock_input = Account.create(
            {
                "code": "TEST4",
                "name": "Stock Input",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        stock_output = Account.create(
            {
                "code": "TEST5",
                "name": "Stock Output",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "test partner",
                "property_account_payable_id": account_payable.id,
                "company_id": cls.company.id,
            }
        )
        stock_journal = cls.env["account.journal"].create(
            {
                "code": "Valuation",
                "name": "Valuation Journal",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.category = cls.env["product.category"].create(
            {
                "name": "Deposit Test Category",
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_account_expense_categ_id": account_expense.id,
                "property_stock_valuation_account_id": stock_valuation.id,
                "property_stock_account_input_categ_id": stock_input.id,
                "property_stock_account_output_categ_id": stock_output.id,
                "property_stock_journal": stock_journal.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Deposit Test Product",
                "type": "product",
                "categ_id": cls.category.id,
                "company_id": cls.company.id,
            }
        )
        cls.account_deposit = Account.create(
            {
                "name": "Purchase Deposit",
                "code": "TEST6",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "code": "TP",
                "name": "Test Purchase",
                "type": "purchase",
                "company_id": cls.company.id,
            }
        )

    def _create_purchase_order(self):
        with Form(self.env["purchase.order"]) as po_form:
            po_form.partner_id = self.vendor
            po_form.date_order = fields.Date.from_string("2025-10-01")
            po_form.company_id = self.company
            po_form.currency_id = self.currency_usd
            with po_form.order_line.new() as line:
                line.product_id = self.product
                line.product_qty = 1.0
                line.price_unit = 100.0
        po = po_form.save()
        po.button_confirm()
        return po

    def create_advance_payment(self, po):
        wizard_env = self.env["purchase.advance.payment.inv"].with_context(
            active_id=po.id,
            active_ids=po.ids,
            active_model="purchase.order",
            create_bills=True,
        )
        with Form(wizard_env) as advance_form:
            advance_form.advance_payment_method = "percentage"
            advance_form.amount = 50
            advance_form.deposit_account_id = self.account_deposit
        wizard = advance_form.save()
        wizard.create_invoices()

    def test_preserve_deposit_amount_on_vendor_bill(self):
        po = self._create_purchase_order()
        self.create_advance_payment(po)
        po.invoice_ids.invoice_date = fields.Date.from_string("2025-10-01")
        deposit_line = po.invoice_ids.line_ids.filtered(
            lambda l: l.move_id.is_deposit and l.purchase_line_id.is_deposit
        )
        self.assertTrue(deposit_line, "Deposit bill should have a deposit line.")
        po.invoice_ids.action_post()
        original_deposit_balance = deposit_line.balance
        po.picking_ids.move_ids.write({"quantity_done": 1})
        po.picking_ids.button_validate()
        res = po.with_context(create_bill=True).action_create_invoice()
        bill = self.env["account.move"].browse(res["res_id"])
        bill.invoice_date = fields.Date.today()
        bill.action_post()
        bill_deposit_line = bill.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit
        )
        self.assertTrue(
            bill_deposit_line,
            "Vendor bill created from PO should contain a deposit line.",
        )
        self.assertEqual(abs(bill_deposit_line.balance), original_deposit_balance)
        svls = bill.line_ids.mapped("stock_valuation_layer_ids")
        self.assertEqual(svls.value, -500.0)
