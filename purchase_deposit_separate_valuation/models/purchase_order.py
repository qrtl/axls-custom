# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import Command, _, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    use_separate_valuation = fields.Boolean(
        string="Separate Valuation Mode",
        copy=False,
        help="When enabled, vendor bills linked to this purchase order do "
        "not trigger price-difference stock valuation layers. Any residual "
        "on the Stock-Input (GRNI) account caused by the difference between "
        "the receipt cost and the billed amount is closed out to the "
        "configured Separate-Valuation GRNI Adjustment Account.",
    )
    sep_val_grni_adjustment_move_id = fields.Many2one(
        "account.move",
        string="Separate-Valuation GRNI Adjustment",
        copy=False,
        readonly=True,
        help="Latest GRNI adjustment journal entry posted to close the "
        "Stock-Input residual for this purchase order.",
    )

    def action_view_sep_val_grni_adjustment(self):
        self.ensure_one()
        move = self.sep_val_grni_adjustment_move_id
        if not move:
            return {"type": "ir.actions.act_window_close"}
        return {
            "type": "ir.actions.act_window",
            "name": _("GRNI Adjustment"),
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": move.id,
            "context": {"create": False},
        }

    def _sync_sep_val_grni_adjustment(self):
        """Re-compute and (re)post the GRNI adjustment entry for this PO.

        Called from ``account.move._post`` (and after draft/cancel) whenever
        a vendor bill linked to a Separate-Valuation PO changes state. Only
        fires once every stockable product line is fully invoiced — until
        then a residual is expected and posting an adjustment would be
        premature.
        """
        for order in self:
            order._sync_sep_val_grni_adjustment_one()

    def _sync_sep_val_grni_adjustment_one(self):
        self.ensure_one()
        if not self.use_separate_valuation:
            return

        if not self._is_sep_val_fully_invoiced():
            if self.sep_val_grni_adjustment_move_id:
                self._remove_sep_val_grni_adjustment()
            return

        stock_input_account_ids = self._get_sep_val_stock_input_account_ids()
        balances = self._compute_sep_val_grni_balances(stock_input_account_ids)
        rounding = self.company_id.currency_id.rounding
        meaningful = {
            account_id: balance
            for account_id, balance in balances.items()
            if not float_is_zero(balance, precision_rounding=rounding)
        }

        if self.sep_val_grni_adjustment_move_id:
            self._remove_sep_val_grni_adjustment()

        if not meaningful:
            return

        adjustment_account = self.company_id.sep_val_grni_adjustment_account_id
        if not adjustment_account:
            raise UserError(
                _(
                    "Please configure the Separate-Valuation GRNI Adjustment "
                    "Account on company '%s' before posting a vendor bill "
                    "for purchase order '%s'."
                )
                % (self.company_id.display_name, self.display_name)
            )

        journal = self._get_sep_val_grni_adjustment_journal()
        line_vals = []
        for account_id, balance in meaningful.items():
            amount = abs(balance)
            if balance > 0:
                # Bill side exceeded receipt side: stock_input has a debit
                # residual. Credit it, debit the adjustment account (loss).
                line_vals.append(
                    Command.create(
                        {
                            "name": _("Sep-Val GRNI Adjustment"),
                            "account_id": account_id,
                            "credit": amount,
                            "debit": 0.0,
                        }
                    )
                )
                line_vals.append(
                    Command.create(
                        {
                            "name": _("Sep-Val GRNI Adjustment"),
                            "account_id": adjustment_account.id,
                            "debit": amount,
                            "credit": 0.0,
                        }
                    )
                )
            else:
                # Receipt side exceeded bill side: stock_input has a credit
                # residual. Debit it, credit the adjustment account (gain).
                line_vals.append(
                    Command.create(
                        {
                            "name": _("Sep-Val GRNI Adjustment"),
                            "account_id": account_id,
                            "debit": amount,
                            "credit": 0.0,
                        }
                    )
                )
                line_vals.append(
                    Command.create(
                        {
                            "name": _("Sep-Val GRNI Adjustment"),
                            "account_id": adjustment_account.id,
                            "credit": amount,
                            "debit": 0.0,
                        }
                    )
                )

        adjustment = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": fields.Date.context_today(self),
                "ref": _("Sep-Val GRNI Adjustment - %s") % self.name,
                "line_ids": line_vals,
            }
        )
        adjustment.action_post()
        self.sep_val_grni_adjustment_move_id = adjustment

    def _remove_sep_val_grni_adjustment(self):
        self.ensure_one()
        adj = self.sep_val_grni_adjustment_move_id
        if not adj:
            return
        try:
            if adj.state == "posted":
                adj.button_draft()
            adj.unlink()
        except Exception as err:
            raise UserError(
                _(
                    "Could not remove the previous GRNI adjustment entry "
                    "'%s'. Please unreconcile or manually reverse it first.\n"
                    "Details: %s"
                )
                % (adj.display_name, err)
            )
        self.sep_val_grni_adjustment_move_id = False

    def _is_sep_val_fully_invoiced(self):
        """Return True iff every stockable PO line has been fully covered
        by **posted** vendor bills.

        Standard Odoo's ``qty_invoiced`` also counts lines from bills in
        draft state, but for the GRNI adjustment we want to mirror what is
        actually in the ledger — otherwise resetting a bill to draft would
        leave the PO looking fully invoiced from a qty perspective while
        the bill's stock-input balance is no longer recorded, producing
        a spurious adjustment for the receipt-only residual.
        """
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        product_lines = self.order_line.filtered(
            lambda l: not l.display_type and l.product_id.type == "product"
        )
        if not product_lines:
            return True
        for line in product_lines:
            posted_qty = 0.0
            for inv_line in line.invoice_lines:
                move = inv_line.move_id
                if move.state != "posted":
                    continue
                qty = inv_line.product_uom_id._compute_quantity(
                    inv_line.quantity, line.product_uom
                )
                if move.move_type == "in_invoice":
                    posted_qty += qty
                elif move.move_type == "in_refund":
                    posted_qty -= qty
            if (
                float_compare(
                    posted_qty,
                    line.qty_received,
                    precision_digits=precision,
                )
                < 0
            ):
                return False
        return True

    def _get_sep_val_stock_input_account_ids(self):
        self.ensure_one()
        account_ids = set()
        for line in self.order_line.filtered(
            lambda l: l.product_id
            and l.product_id.type == "product"
            and l.product_id.categ_id.property_valuation == "real_time"
        ):
            accounts = line.product_id.product_tmpl_id.get_product_accounts(
                fiscal_pos=self.fiscal_position_id
            )
            stock_input = accounts.get("stock_input")
            if stock_input:
                account_ids.add(stock_input.id)
        return account_ids

    def _compute_sep_val_grni_balances(self, stock_input_account_ids):
        """Sum balances on Stock-Input accounts from receipt moves AND posted
        vendor bills linked to this PO. The adjustment entry itself is
        excluded by checking the move_type.
        """
        self.ensure_one()
        balances = {}
        if not stock_input_account_ids:
            return balances

        done_moves = self.order_line.mapped("move_ids").filtered(
            lambda m: m.state == "done"
            and m.product_id
            and m.product_id.type == "product"
            and m.product_id.categ_id.property_valuation == "real_time"
        )
        receipt_amls = done_moves.mapped("account_move_ids.line_ids").filtered(
            lambda l: l.account_id.id in stock_input_account_ids
            and l.move_id.state == "posted"
        )
        for aml in receipt_amls:
            balances.setdefault(aml.account_id.id, 0.0)
            balances[aml.account_id.id] += aml.balance

        bill_ids = self.invoice_ids.filtered(lambda m: m.state == "posted").ids
        if bill_ids:
            bill_amls = self.env["account.move.line"].search(
                [
                    ("move_id", "in", bill_ids),
                    ("account_id", "in", list(stock_input_account_ids)),
                ]
            )
            for aml in bill_amls:
                balances.setdefault(aml.account_id.id, 0.0)
                balances[aml.account_id.id] += aml.balance

        return balances

    def _get_sep_val_grni_adjustment_journal(self):
        self.ensure_one()
        journal = self.company_id.sep_val_grni_adjustment_journal_id
        if journal:
            return journal
        journal = self.env["account.journal"].search(
            [
                ("type", "=", "general"),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if not journal:
            raise UserError(
                _(
                    "No General journal was found for company '%s'. Please "
                    "configure the Separate-Valuation GRNI Adjustment Journal."
                )
                % self.company_id.display_name
            )
        return journal
