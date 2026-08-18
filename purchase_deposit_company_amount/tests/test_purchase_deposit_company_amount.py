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
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Deposit Test Product B",
                "type": "product",
                "categ_id": cls.category.id,
                "company_id": cls.company.id,
            }
        )
        cls.product_c = cls.env["product.product"].create(
            {
                "name": "Deposit Test Product C",
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    DEPOSIT_DATE = "2025-10-01"  # USD 1 = JPY 150
    FINAL_DATE = "2025-11-01"  # USD 1 = JPY 160

    def _create_purchase_order(self, lines=None):
        """Confirmed USD purchase order. Defaults to a single USD 100 line;
        pass ``[(product, price), ...]`` for more, all at quantity 1 so one
        receipt validates them together.
        """
        lines = lines or [(self.product, 100.0)]
        with Form(self.env["purchase.order"]) as po_form:
            po_form.partner_id = self.vendor
            po_form.date_order = fields.Date.from_string(self.DEPOSIT_DATE)
            po_form.company_id = self.company
            po_form.currency_id = self.currency_usd
            for product, price in lines:
                with po_form.order_line.new() as line:
                    line.product_id = product
                    line.product_qty = 1.0
                    line.price_unit = price
        po = po_form.save()
        po.button_confirm()
        return po

    def _register_deposit(self, po, percentage=30):
        wizard_env = self.env["purchase.advance.payment.inv"].with_context(
            active_id=po.id,
            active_ids=po.ids,
            active_model="purchase.order",
            create_bills=True,
        )
        with Form(wizard_env) as advance_form:
            advance_form.advance_payment_method = "percentage"
            advance_form.amount = percentage
            advance_form.deposit_account_id = self.account_deposit
        advance_form.save().create_invoices()
        deposit_bill = po.invoice_ids
        deposit_bill.invoice_date = fields.Date.from_string(self.DEPOSIT_DATE)
        return deposit_bill

    def _post_deposit_bill(self, po, company_amount, percentage=30):
        """Register a deposit, pin it to the amount actually paid, post it."""
        deposit_bill = self._register_deposit(po, percentage)
        self._deposit_line(deposit_bill).company_amount = company_amount
        deposit_bill.action_post()
        return deposit_bill

    def _create_final_bill(self, po):
        po.picking_ids.move_ids.write({"quantity_done": 1})
        po.picking_ids.button_validate()
        res = po.with_context(create_bill=True).action_create_invoice()
        bill = self.env["account.move"].browse(res["res_id"])
        bill.invoice_date = fields.Date.from_string(self.FINAL_DATE)
        return bill

    def _create_bill_without_deposit(self):
        """A plain foreign-currency vendor bill, no purchase deposit involved."""
        return self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "journal_id": self.journal.id,
                "currency_id": self.currency_usd.id,
                "invoice_date": fields.Date.from_string(self.FINAL_DATE),
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

    def _deposit_line(self, move):
        """The deposit bill's own line, which the positive quantity picks out."""
        return move.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit and l.quantity > 0
        )

    def _offset_line(self, move):
        """The final bill's deposit offset: same purchase order line, negated."""
        return move.line_ids.filtered(
            lambda l: l.purchase_line_id.is_deposit and l.quantity < 0
        )

    def _goods_lines(self, move):
        return move.line_ids.filtered(
            lambda l: l.display_type == "product" and not l.purchase_line_id.is_deposit
        )

    def _goods_line(self, move, product):
        return self._goods_lines(move).filtered(lambda l: l.product_id == product)

    def _payable_line(self, move):
        return move.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
        )

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    def test_deposit_rate_difference_lands_on_the_goods(self):
        """The end-to-end outcome, which no single line of the implementation
        states. USD 100 order, USD 30 deposit settled for 3900, final bill at
        rate 160: the offset stays pinned to the 3900 really paid, the goods
        carry the true cost (3900 + 70*160), the payable is exactly the
        remaining USD 70 at the current rate, and the valuation layer follows
        the goods rather than the rate.
        """
        po = self._create_purchase_order()
        self._post_deposit_bill(po, 3900)
        self.assertEqual(
            po.order_line.filtered("is_deposit").deposit_company_amount, 3900
        )
        bill = self._create_final_bill(po)
        goods_line = self._goods_lines(bill)
        self.assertEqual(self._offset_line(bill).balance, -3900)
        self.assertEqual(goods_line.balance, 15100)
        self.assertEqual(self._payable_line(bill).balance, -11200)
        # The difference is booked into the goods, not parked on the override:
        # company_amount stays empty and keeps meaning "the user typed this".
        self.assertFalse(goods_line.company_amount)
        # purchase_stock divides the gross unit price back by currency_rate, so
        # it has to round trip to the overridden balance, not the rate-based one.
        self.assertAlmostEqual(
            goods_line._get_gross_unit_price()
            / goods_line.currency_rate
            * goods_line.quantity,
            goods_line.balance,
            places=2,
        )
        self.assertNotAlmostEqual(
            goods_line.balance, goods_line._get_rate_based_balance(), places=2
        )
        bill.action_post()
        self.assertEqual(self._offset_line(bill).balance, -3900)
        self.assertEqual(goods_line.balance, 15100)
        self.assertEqual(self._payable_line(bill).balance, -11200)
        self.assertEqual(
            sum(bill.line_ids.mapped("stock_valuation_layer_ids").mapped("value")),
            -900.0,
        )

    def test_rate_difference_is_prorated_across_goods_lines(self):
        """With more than one goods line the difference is split by value, and
        the last line sweeps up the rounding so the shares still add back to it
        exactly. A single-line order reaches neither: it takes the remainder
        branch on the first pass, leaving the weighting and the sweep untested.

        USD 20 + 30 + 50, deposit USD 30 settled for 3801, final rate 160. The
        difference is -999, which the weights turn into -199.8, -299.7 and
        -499.5. Rounded on their own those are -200, -300 and -500, one yen more
        than there is to give away, so the last line has to take -499 instead.
        """
        po = self._create_purchase_order(
            [(self.product, 20.0), (self.product_b, 30.0), (self.product_c, 50.0)]
        )
        self._post_deposit_bill(po, 3801)
        bill = self._create_final_bill(po)
        line_a = self._goods_line(bill, self.product)
        line_b = self._goods_line(bill, self.product_b)
        line_c = self._goods_line(bill, self.product_c)
        # Rate-based 3200, 4800 and 8000, less the shares. Line A pins the
        # weighting: an equal split would have given it -333, not -200.
        self.assertEqual(line_a.balance, 3000)
        self.assertEqual(line_b.balance, 4500)
        # Line C pins the sweep: rounding its own share would give 7500.
        self.assertEqual(line_c.balance, 7501)
        self.assertEqual(self._offset_line(bill).balance, -3801)
        # The shares add back to the difference exactly, which is what leaves
        # the payable at the remaining USD 70 converted at the current rate
        # rather than a yen out.
        self.assertEqual(line_a.balance + line_b.balance + line_c.balance - 16000, -999)
        self.assertEqual(self._payable_line(bill).balance, -11200)
        bill.action_post()
        self.assertEqual(
            sum(bill.line_ids.mapped("stock_valuation_layer_ids").mapped("value")),
            -999.0,
        )

    def test_deposit_value_is_read_back_from_the_ledger(self):
        """The deposit value must be derived from posted bill lines, not
        snapshotted when the deposit bill is posted. Defends against going back
        to a stored field written in action_post, under which resetting or
        reversing the deposit bill leaves the purchase order still handing a
        stale amount to the final bill.
        """
        po = self._create_purchase_order()
        deposit_bill = self._post_deposit_bill(po, 3900)
        deposit_po_line = po.order_line.filtered("is_deposit")
        self.assertEqual(deposit_po_line.deposit_company_amount, 3900)
        deposit_bill.button_draft()
        self.assertEqual(deposit_po_line.deposit_company_amount, 0)

    def test_only_the_deposit_bill_may_be_pinned(self):
        """Both lines of the final bill refuse the override. The offset is the
        same purchase order line as the deposit's and so looks eligible on every
        test but the sign, while its value is derived from the posted deposit
        bill and typing over it would quietly untie the two.
        """
        po = self._create_purchase_order()
        deposit_bill = self._post_deposit_bill(po, 3900)
        self.assertTrue(deposit_bill.is_deposit)
        bill = self._create_final_bill(po)
        # The two move-level concepts are disjoint, and the final bill is where
        # they part company: nobody may type on it, yet its goods line's balance
        # IS pinned, so stock valuation has to keep following it. Gating
        # valuation on is_deposit instead zeroes the adjustment.
        self.assertFalse(bill.is_deposit)
        self.assertTrue(bill._get_deposit_offset_lines())
        with self.assertRaises(ValidationError):
            self._goods_lines(bill).company_amount = 17000
        with self.assertRaises(ValidationError):
            self._offset_line(bill).company_amount = 3000

    def test_plain_vendor_bill_is_untouched(self):
        """A bill with no deposit keeps Odoo's rate-based balance and refuses
        the override. The module hooks _sync_invoice, which runs for every
        invoice line in the database, so both halves are worth stating.
        """
        bill = self._create_bill_without_deposit()
        line = bill.invoice_line_ids
        self.assertFalse(bill.is_deposit)
        self.assertEqual(line.balance, 16000)  # USD 100 at the 2025-11-01 rate
        with self.assertRaises(ValidationError):
            line.company_amount = 17000

    def test_changing_the_bill_date_rebalances_the_deposit_bill(self):
        """Editing the bill date moves currency_rate, so the standard sync
        re-derives every balance from the new rate, payable included, while the
        override puts the deposit line straight back. The needed totals come out
        identical, Odoo's payment-term sync concludes there is nothing to do,
        and the bill would be left unbalanced.
        """
        po = self._create_purchase_order()
        deposit_bill = self._register_deposit(po)
        deposit_bill.invoice_date = fields.Date.from_string(self.FINAL_DATE)
        deposit_line = self._deposit_line(deposit_bill)
        deposit_line.company_amount = 3900
        self.assertEqual(deposit_line.balance, 3900)
        # Back-date the bill: USD 1 = JPY 150 instead of 160.
        deposit_bill.invoice_date = fields.Date.from_string(self.DEPOSIT_DATE)
        self.assertEqual(deposit_line.balance, 3900)
        self.assertEqual(self._payable_line(deposit_bill).balance, -3900)
        deposit_bill.action_post()

    def test_changing_the_bill_date_on_the_final_bill(self):
        """The counterpart, which needs no such help. Back-dating the final bill
        re-derives the goods at the new rate while the offset stays pinned, so
        the move's total does shift and Odoo's own payment-term sync notices.
        """
        po = self._create_purchase_order()
        self._post_deposit_bill(po, 3900)
        bill = self._create_final_bill(po)
        bill.invoice_date = fields.Date.from_string(self.DEPOSIT_DATE)
        # Rate 150: goods 15000 less the 600 rate difference on the deposit.
        self.assertEqual(self._offset_line(bill).balance, -3900)
        self.assertEqual(self._goods_lines(bill).balance, 14400)
        self.assertEqual(self._payable_line(bill).balance, -10500)
        bill.action_post()
