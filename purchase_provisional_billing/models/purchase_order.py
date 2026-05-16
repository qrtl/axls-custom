# Copyright 2025 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    separate_valuation = fields.Boolean(
        string="Separate Valuation Mode",
        copy=False,
        help="When enabled, advance bills are used for interim invoicing and "
        "stock valuation is not affected by vendor bills.",
    )
    sep_val_advance_bill_ids = fields.One2many(
        "account.move",
        "sep_val_purchase_id",
        domain=[("sep_val_move_type", "=", "advance_bill")],
        string="Advance Bills",
    )
    sep_val_final_bill_id = fields.Many2one(
        "account.move",
        string="Final Bill",
        copy=False,
    )
    sep_val_application_credit_note_ids = fields.One2many(
        "account.move",
        "sep_val_purchase_id",
        domain=[("sep_val_move_type", "=", "advance_application")],
        string="Application Credit Notes",
    )
    sep_val_adjustment_entry_ids = fields.One2many(
        "account.move",
        "sep_val_purchase_id",
        domain=[("sep_val_move_type", "=", "adjustment_entry")],
        string="Adjustment Entries",
    )
    sep_val_advance_total = fields.Monetary(
        string="Advance Total",
        compute="_compute_sep_val_advance_totals",
        currency_field="currency_id",
        help="Sum of posted Advance Bills converted to PO currency.",
    )
    sep_val_applied_total = fields.Monetary(
        string="Applied Total",
        compute="_compute_sep_val_advance_totals",
        currency_field="currency_id",
        help="Sum of posted Application Credit Notes converted to PO currency.",
    )
    sep_val_unapplied_advance_total = fields.Monetary(
        string="Unapplied Advance",
        compute="_compute_sep_val_advance_totals",
        currency_field="currency_id",
        help="Advance Total minus Applied Total.",
    )

    @api.depends(
        "sep_val_advance_bill_ids.state",
        "sep_val_advance_bill_ids.amount_untaxed",
        "sep_val_advance_bill_ids.currency_id",
        "sep_val_advance_bill_ids.invoice_date",
        "sep_val_application_credit_note_ids.state",
        "sep_val_application_credit_note_ids.amount_untaxed",
        "sep_val_application_credit_note_ids.currency_id",
        "sep_val_application_credit_note_ids.invoice_date",
        "currency_id",
    )
    def _compute_sep_val_advance_totals(self):
        for order in self:
            posted_bills = order.sep_val_advance_bill_ids.filtered(
                lambda m: m.state == "posted"
            )
            advance_total = sum(
                bill.currency_id._convert(
                    bill.amount_untaxed,
                    order.currency_id,
                    order.company_id,
                    bill.invoice_date or fields.Date.today(),
                )
                for bill in posted_bills
            )
            posted_notes = order.sep_val_application_credit_note_ids.filtered(
                lambda m: m.state == "posted"
            )
            applied_total = sum(
                note.currency_id._convert(
                    note.amount_untaxed,
                    order.currency_id,
                    order.company_id,
                    note.invoice_date or fields.Date.today(),
                )
                for note in posted_notes
            )
            order.sep_val_advance_total = advance_total
            order.sep_val_applied_total = applied_total
            order.sep_val_unapplied_advance_total = advance_total - applied_total

    def action_create_invoice(self):
        sep_val_orders = self.filtered("separate_valuation")
        if sep_val_orders:
            raise UserError(
                _(
                    "Purchase order(s) %s use Separate Valuation Mode. "
                    "Please use the dedicated Advance/Final Bill buttons instead."
                )
                % ", ".join(sep_val_orders.mapped("name"))
            )
        return super().action_create_invoice()

    def action_create_advance_bill(self):
        self.ensure_one()
        if self.sep_val_final_bill_id:
            raise UserError(
                _(
                    "A Final Bill already exists for purchase order '%s'. "
                    "You cannot create a new advance bill after the final bill."
                )
                % self.name
            )
        order = self.with_company(self.company_id)
        invoice_vals = order._prepare_invoice()
        invoice_vals["sep_val_move_type"] = "advance_bill"
        invoice_vals["sep_val_purchase_id"] = order.id

        sequence = 10
        pending_section = None
        for line in order.order_line:
            if line.display_type == "line_section":
                pending_section = line
                continue
            if line.display_type:
                if line.display_type == "line_note":
                    note_vals = line._prepare_account_move_line()
                    note_vals["sequence"] = sequence
                    invoice_vals["invoice_line_ids"].append(Command.create(note_vals))
                    sequence += 1
                continue
            if pending_section:
                section_vals = pending_section._prepare_account_move_line()
                section_vals["sequence"] = sequence
                invoice_vals["invoice_line_ids"].append(Command.create(section_vals))
                sequence += 1
                pending_section = None
            line_vals = line._prepare_account_move_line()
            line_vals.pop("product_id", None)
            line_vals.pop("purchase_line_id", None)
            line_vals["account_id"] = order._get_sep_val_advance_account(line).id
            line_vals["tax_ids"] = False
            line_vals["quantity"] = line.product_qty
            line_vals["sequence"] = sequence
            invoice_vals["invoice_line_ids"].append(Command.create(line_vals))
            sequence += 1

        bill = (
            self.env["account.move"]
            .with_context(default_move_type="in_invoice")
            .create(invoice_vals)
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Advance Bill"),
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": bill.id,
        }

    def action_create_final_bill(self):
        self.ensure_one()
        if self.sep_val_final_bill_id:
            raise UserError(
                _(
                    "A Final Bill already exists for purchase order '%s'. "
                    "Please unset or delete it before creating a new one."
                )
                % self.name
            )
        if not self._check_all_received():
            raise UserError(
                _(
                    "Cannot create Final Bill for '%s': some receipt-tracked "
                    "items have not been fully received yet."
                )
                % self.name
            )
        draft_advances = self.sep_val_advance_bill_ids.filtered(
            lambda m: m.state == "draft"
        )
        if draft_advances:
            raise UserError(
                _(
                    "Please post or cancel all draft Advance Bills before "
                    "creating the Final Bill for '%s'."
                )
                % self.name
            )

        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        invoiceable_lines = self.order_line.filtered(
            lambda l: not l.display_type
            and not float_is_zero(l.qty_to_invoice, precision_digits=precision)
        )
        if not invoiceable_lines:
            raise UserError(
                _(
                    "No invoiceable lines found on purchase order '%s'. "
                    "All items may already be fully invoiced."
                )
                % self.name
            )

        order = self.with_company(self.company_id)
        invoice_vals = order._prepare_invoice()
        invoice_vals["sep_val_move_type"] = "final_bill"
        invoice_vals["sep_val_purchase_id"] = order.id

        sequence = 10
        pending_section = None
        for line in order.order_line:
            if line.display_type == "line_section":
                pending_section = line
                continue
            if line.display_type:
                continue
            if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if pending_section:
                section_vals = pending_section._prepare_account_move_line()
                section_vals["sequence"] = sequence
                invoice_vals["invoice_line_ids"].append(Command.create(section_vals))
                sequence += 1
                pending_section = None
            line_vals = line._prepare_account_move_line()
            line_vals["sequence"] = sequence
            invoice_vals["invoice_line_ids"].append(Command.create(line_vals))
            sequence += 1

        bill = (
            self.env["account.move"]
            .with_context(default_move_type="in_invoice")
            .create(invoice_vals)
        )
        self.sep_val_final_bill_id = bill
        return {
            "type": "ir.actions.act_window",
            "name": _("Final Bill"),
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": bill.id,
        }

    def action_view_advance_bills(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Advance Bills"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [
                ("sep_val_purchase_id", "=", self.id),
                ("sep_val_move_type", "=", "advance_bill"),
            ],
            "context": {"create": False},
        }

    def action_view_sep_val_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Separate Valuation Documents"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [
                ("sep_val_purchase_id", "=", self.id),
                (
                    "sep_val_move_type",
                    "in",
                    ("final_bill", "advance_application", "adjustment_entry"),
                ),
            ],
            "context": {"create": False},
        }

    def action_unset_final_bill(self):
        self.ensure_one()
        final = self.sep_val_final_bill_id
        if not final:
            return {"type": "ir.actions.act_window_close"}
        if final.state == "posted":
            raise UserError(
                _(
                    "The Final Bill '%s' is posted and has been reconciled with "
                    "advance credit notes. Please reset it to draft (which will "
                    "also break the reconciliation) before unsetting."
                )
                % final.name
            )
        final.write(
            {
                "sep_val_move_type": False,
                "sep_val_purchase_id": False,
            }
        )
        self.sep_val_final_bill_id = False

    def _check_all_received(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in self.order_line.filtered(
            lambda l: not l.display_type
            and l.product_id.purchase_method == "receive"
        ):
            if (
                float_compare(
                    line.qty_received,
                    line.product_qty,
                    precision_digits=precision,
                )
                < 0
            ):
                return False
        return True

    def _get_sep_val_advance_account(self, line):
        self.ensure_one()
        accounts = line.product_id.product_tmpl_id.get_product_accounts(
            fiscal_pos=self.fiscal_position_id
        )
        account = accounts.get("expense")
        if account:
            return account
        raise UserError(
            _(
                "Could not determine an account for purchase order line '%s'. "
                "Please configure the product or category expense account."
            )
            % line.name
        )

    def _prepare_advance_credit_note_vals(self, advance_bill):
        self.ensure_one()
        advance_lines = advance_bill.invoice_line_ids
        if not advance_lines:
            raise UserError(
                _(
                    "Advance Bill '%s' has no invoice lines to derive the application "
                    "credit note from."
                )
                % advance_bill.display_name
            )
        line_commands = []
        for line in advance_lines:
            if line.display_type:
                line_commands.append(
                    Command.create(
                        {
                            "display_type": line.display_type,
                            "name": line.name,
                            "sequence": line.sequence,
                        }
                    )
                )
                continue
            line_commands.append(
                Command.create(
                    {
                        "name": _("Reverse Advance: %s") % line.name,
                        "quantity": line.quantity,
                        "account_id": line.account_id.id,
                        "price_unit": line.price_unit,
                        "tax_ids": False,
                        "analytic_distribution": line.analytic_distribution,
                        "sequence": line.sequence,
                    }
                )
            )
        return {
            "move_type": "in_refund",
            "partner_id": self.partner_id.id,
            "invoice_origin": self.name,
            "invoice_date": advance_bill.invoice_date or fields.Date.today(),
            "currency_id": advance_bill.currency_id.id,
            "fiscal_position_id": self.fiscal_position_id.id,
            "company_id": self.company_id.id,
            "sep_val_move_type": "advance_application",
            "sep_val_purchase_id": self.id,
            "sep_val_origin_move_id": advance_bill.id,
            "invoice_line_ids": line_commands,
        }

    def _create_paired_credit_note(self, advance_bill):
        """Create and post a credit note that reverses the advance bill.

        Called from ``account.move._post`` when an advance bill is posted.
        The credit note mirrors the advance bill 1:1 so the P&L impact of
        the pair is zero. The AP-side line stays unreconciled until the
        final bill is posted, at which point it is offset against the
        final bill's payable line.
        """
        self.ensure_one()
        existing = advance_bill.sep_val_application_move_ids.filtered(
            lambda m: m.state != "cancel"
        )
        if existing:
            return existing[:1]
        vals = self._prepare_advance_credit_note_vals(advance_bill)
        credit_note = self.env["account.move"].create(vals)
        credit_note.action_post()
        return credit_note

    def _settle_final_bill(self, final_bill):
        """Reconcile the final bill payable line with paired credit notes.

        Any residual difference is posted to the adjustment account via a
        separate journal entry, then all payable lines are reconciled
        together so the final bill (and credit notes) are marked paid.
        """
        self.ensure_one()
        company = self.company_id
        payable_account = final_bill.partner_id.with_company(
            company
        ).property_account_payable_id
        if not payable_account:
            raise UserError(
                _("Vendor '%s' has no payable account configured.")
                % final_bill.partner_id.display_name
            )

        final_ap_lines = final_bill.line_ids.filtered(
            lambda l: l.account_id == payable_account and not l.reconciled
        )
        cn_ap_lines = self.sep_val_application_credit_note_ids.filtered(
            lambda m: m.state == "posted"
        ).line_ids.filtered(
            lambda l: l.account_id == payable_account and not l.reconciled
        )
        ap_lines = final_ap_lines | cn_ap_lines
        if not ap_lines:
            return

        balance_sum = sum(ap_lines.mapped("balance"))
        rounding = company.currency_id.rounding

        adjustment = self.env["account.move"]
        if not float_is_zero(balance_sum, precision_rounding=rounding):
            adjustment = self._create_settlement_adjustment(
                final_bill, payable_account, balance_sum
            )
            ap_lines |= adjustment.line_ids.filtered(
                lambda l: l.account_id == payable_account
            )

        ap_lines.reconcile()
        self.sep_val_application_credit_note_ids.filtered(
            lambda m: m.state == "posted" and not m.sep_val_target_move_id
        ).write({"sep_val_target_move_id": final_bill.id})
        return adjustment

    def _create_settlement_adjustment(self, final_bill, payable_account, balance_sum):
        company = self.company_id
        adjustment_account = company.sep_val_variance_account_id
        if not adjustment_account:
            raise UserError(
                _(
                    "Please configure the Settlement Adjustment Account in "
                    "Accounting settings before posting the Final Bill."
                )
            )
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", company.id)],
            limit=1,
        )
        if not journal:
            raise UserError(
                _("No Miscellaneous journal was found for company '%s'.")
                % company.display_name
            )

        # ap_offset is what we must add on the payable side to bring the
        # combined balance back to zero (so the reconciliation closes out).
        ap_offset = -balance_sum
        ref = _("PO Settlement Adjustment - %s") % self.name
        line_vals = [
            Command.create(
                {
                    "account_id": payable_account.id,
                    "partner_id": final_bill.partner_id.id,
                    "name": ref,
                    "debit": ap_offset if ap_offset > 0 else 0.0,
                    "credit": -ap_offset if ap_offset < 0 else 0.0,
                }
            ),
            Command.create(
                {
                    "account_id": adjustment_account.id,
                    "name": ref,
                    "debit": balance_sum if balance_sum > 0 else 0.0,
                    "credit": -balance_sum if balance_sum < 0 else 0.0,
                }
            ),
        ]
        adjustment = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": final_bill.invoice_date or fields.Date.today(),
                "ref": ref,
                "company_id": company.id,
                "line_ids": line_vals,
                "sep_val_move_type": "adjustment_entry",
                "sep_val_purchase_id": self.id,
            }
        )
        adjustment.action_post()
        return adjustment
