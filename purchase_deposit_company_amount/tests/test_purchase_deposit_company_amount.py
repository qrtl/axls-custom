# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase


class TestPurchaseDepositCompanyAmount(TransactionCase):
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

    def _create_final_bill(self, po):
        po.picking_ids.move_ids.write({"quantity_done": 1})
        po.picking_ids.button_validate()
        res = po.with_context(create_bill=True).action_create_invoice()
        bill = self.env["account.move"].browse(res["res_id"])
        bill.invoice_date = fields.Date.from_string("2025-11-01")
        return bill

    def _post_deposit_bill(self, po, company_amount):
        deposit_bill = po.invoice_ids
        deposit_bill.invoice_date = fields.Date.from_string("2025-10-01")
        deposit_line = deposit_bill.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit and l.quantity > 0
        )
        deposit_line.company_amount = company_amount
        deposit_bill.action_post()
        return deposit_bill, deposit_line

    def _create_bill_without_deposit(self):
        """A plain foreign-currency vendor bill, no purchase deposit involved."""
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "journal_id": self.journal.id,
                "currency_id": self.currency_usd.id,
                "invoice_date": fields.Date.from_string("2025-11-01"),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        return bill, bill.invoice_line_ids

    def test_deposit_rate_difference_lands_on_product_line(self):
        """The end-to-end accounting outcome, which no single line of the
        implementation states: USD 100 PO, USD 30 deposit settled for 3900,
        final bill at rate 160. The offset must stay pinned to the 3900 really
        paid, the goods must carry the true cost (3900 + 70*160 = 15100), the
        payable must be exactly the remaining USD 70 at the current rate, and
        the valuation layer must follow the goods rather than the rate.
        """
        po = self._create_purchase_order()
        self._create_advance_payment(po)
        _deposit_bill, deposit_line = self._post_deposit_bill(po, 3900)
        self.assertEqual(deposit_line.balance, 3900)
        deposit_po_line = po.order_line.filtered("is_deposit")
        self.assertEqual(deposit_po_line.deposit_company_amount, 3900)
        bill = self._create_final_bill(po)
        offset_line = bill.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit and l.quantity < 0
        )
        product_line = bill.line_ids.filtered(
            lambda l: l.display_type == "product" and not l.purchase_line_id.is_deposit
        )
        payable_line = bill.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
        )
        self.assertEqual(offset_line.balance, -3900)
        self.assertEqual(product_line.balance, 15100)
        self.assertEqual(payable_line.balance, -11200)
        # The rate difference is booked into the goods, not parked on a manual
        # override: company_amount stays empty and means "the user typed this".
        self.assertFalse(product_line.company_amount)
        bill.action_post()
        self.assertEqual(offset_line.balance, -3900)
        self.assertEqual(product_line.balance, 15100)
        self.assertEqual(payable_line.balance, -11200)
        svls = bill.line_ids.mapped("stock_valuation_layer_ids")
        self.assertEqual(sum(svls.mapped("value")), -900.0)

    def test_manual_product_override_wins_over_rate_difference(self):
        """A hand-priced product line must be left alone by the rate-difference
        distribution. Invisible at the point of change: the distribution reads
        an empty company_amount as its opt-in, so a refactor that spreads the
        delta over every product line would still balance and still post.
        """
        po = self._create_purchase_order()
        self._create_advance_payment(po)
        self._post_deposit_bill(po, 3900)
        bill = self._create_final_bill(po)
        product_line = bill.line_ids.filtered(
            lambda l: l.display_type == "product" and not l.purchase_line_id.is_deposit
        )
        product_line.company_amount = 17000
        # 17000 exactly -- not 17000 less the 900 rate difference.
        self.assertEqual(product_line.balance, 17000)
        payable_line = bill.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
        )
        self.assertEqual(payable_line.balance, -13100)

    def test_deposit_value_is_read_back_from_the_ledger(self):
        """The deposit value must be derived from posted bill lines, not
        snapshotted when the deposit bill is posted. Defends against going back
        to a stored field written in action_post, under which resetting or
        reversing the deposit bill leaves the purchase order still handing a
        stale amount to the final bill.
        """
        po = self._create_purchase_order()
        self._create_advance_payment(po)
        deposit_bill, _deposit_line = self._post_deposit_bill(po, 3900)
        deposit_po_line = po.order_line.filtered("is_deposit")
        self.assertEqual(deposit_po_line.deposit_company_amount, 3900)
        deposit_bill.button_draft()
        self.assertEqual(deposit_po_line.deposit_company_amount, 0)

    def test_removing_the_deposit_line_rejects_the_override(self):
        """The scope rule has to be enforced on the way out as well as the way
        in. Defends the constraint's dependency list: hung off
        account.move.line.company_amount alone it only fires when that field is
        written, so dropping the deposit line from a bill that already carries
        an override slips through and the bill keeps forcing balances it is no
        longer entitled to.
        """
        po = self._create_purchase_order()
        self._create_advance_payment(po)
        self._post_deposit_bill(po, 3900)
        bill = self._create_final_bill(po)
        product_line = bill.line_ids.filtered(
            lambda l: l.display_type == "product" and not l.purchase_line_id.is_deposit
        )
        product_line.company_amount = 17000
        offset_line = bill.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit and l.quantity < 0
        )
        with self.assertRaises(ValidationError):
            bill.write({"line_ids": [Command.unlink(offset_line.id)]})

    def test_standard_conversion_untouched_without_deposit(self):
        """The override hooks _sync_invoice, which runs for every invoice line
        in the database. Defends the scope check inside it: a bill with no
        deposit must keep Odoo's rate-based balance untouched.
        """
        _bill, line = self._create_bill_without_deposit()
        # USD 100 at the 2025-11-01 rate (1 USD = 160 JPY).
        self.assertEqual(line.balance, 16000)

    def test_changing_the_bill_date_rebalances_the_deposit_bill(self):
        """Editing the bill date moves currency_rate, which makes the standard
        sync recompute every line's balance from the rate. The override has to
        be re-applied and the payable rebuilt from it, or the move is left
        unbalanced. Defends the ordering against the payment-term line being
        settled from rate-converted balances instead of overridden ones.
        """
        po = self._create_purchase_order()
        self._create_advance_payment(po)
        deposit_bill = po.invoice_ids
        deposit_bill.invoice_date = fields.Date.from_string("2025-11-01")
        deposit_line = deposit_bill.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit and l.quantity > 0
        )
        deposit_line.company_amount = 3900
        self.assertEqual(deposit_line.balance, 3900)
        # Back-date the bill: USD 1 = JPY 150 instead of 160.
        deposit_bill.invoice_date = fields.Date.from_string("2025-10-01")
        payable_line = deposit_bill.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
        )
        self.assertEqual(deposit_line.balance, 3900)
        self.assertEqual(payable_line.balance, -3900)
        deposit_bill.action_post()

    def test_override_rejected_on_a_plain_vendor_bill(self):
        """A bill with no deposit must refuse the override on a direct write.
        Defends the account.move.line half of the constraint: Odoo 16 ignores
        dotted paths in @api.constrains, so the account.move constraint cannot
        see a value written straight onto a line and this case is only covered
        while the line-level constraint exists.
        """
        _bill, line = self._create_bill_without_deposit()
        self.assertFalse(line.company_amount_allowed)
        with self.assertRaises(ValidationError):
            line.company_amount = 17000
