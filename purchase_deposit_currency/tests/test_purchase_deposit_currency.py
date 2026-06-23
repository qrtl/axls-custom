# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import Form, TransactionCase


class TestPurchaseDepositCurrency(TransactionCase):
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
        # Latest rate, applied to the final invoice (USD 1 = JPY 160).
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

    def _create_advance_payment(self, po):
        wizard_env = self.env["purchase.advance.payment.inv"].with_context(
            active_id=po.id,
            active_ids=po.ids,
            active_model="purchase.order",
            create_bills=True,
        )
        with Form(wizard_env) as advance_form:
            advance_form.advance_payment_method = "percentage"
            advance_form.amount = 30
            advance_form.deposit_account_id = self.account_deposit
        wizard = advance_form.save()
        wizard.create_invoices()

    def test_deposit_rate_difference_lands_on_product_line(self):
        """USD 100 PO, USD 30 deposit paid as JPY 3900 (manual override),
        final invoice at rate 160. The product line must carry the true cost
        (3900 + 70*160 = 15100) and the payable must be the remaining USD 70
        at the current rate (-11200).
        """
        po = self._create_purchase_order()
        self._create_advance_payment(po)
        deposit_bill = po.invoice_ids
        deposit_bill.invoice_date = fields.Date.from_string("2025-10-01")
        deposit_line = deposit_bill.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit and l.quantity > 0
        )
        self.assertTrue(deposit_line, "Deposit bill should have a deposit line.")
        # Manually enter the JPY actually paid for the deposit (not 30*rate).
        deposit_line.company_amount = 3900
        self.assertEqual(deposit_line.balance, 3900)
        deposit_bill.action_post()
        deposit_po_line = po.order_line.filtered("is_deposit")
        self.assertEqual(deposit_po_line.deposit_company_amount, 3900)

        # Receive the goods, then create the final bill.
        po.picking_ids.move_ids.write({"quantity_done": 1})
        po.picking_ids.button_validate()
        res = po.with_context(create_bill=True).action_create_invoice()
        bill = self.env["account.move"].browse(res["res_id"])
        bill.invoice_date = fields.Date.from_string("2025-11-01")

        offset_line = bill.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit and l.quantity < 0
        )
        product_line = bill.line_ids.filtered(
            lambda l: l.display_type == "product"
            and not l.purchase_line_id.is_deposit
        )
        payable_line = bill.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
        )

        # Offset line still pinned to the JPY actually paid for the deposit.
        self.assertEqual(offset_line.balance, -3900)
        # Rate difference (160 vs the 130 effectively paid) lands on the goods.
        self.assertTrue(product_line.deposit_amount_adjusted)
        self.assertEqual(product_line.company_amount, 15100)
        self.assertEqual(product_line.balance, 15100)
        # Remaining USD 70 payable at the current rate.
        self.assertEqual(payable_line.balance, -11200)

        # Posting must not disturb the balances.
        bill.action_post()
        self.assertEqual(offset_line.balance, -3900)
        self.assertEqual(product_line.balance, 15100)
        self.assertEqual(payable_line.balance, -11200)
        # Stock valuation reflects the true acquisition cost.
        svls = bill.line_ids.mapped("stock_valuation_layer_ids")
        self.assertEqual(sum(svls.mapped("value")), -900.0)
