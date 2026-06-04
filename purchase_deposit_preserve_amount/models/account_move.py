# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_deposit = fields.Boolean(compute="_compute_is_deposit")

    def _compute_is_deposit(self):
        for rec in self:
            rec.is_deposit = any(
                rec.invoice_line_ids.filtered(
                    lambda line: line.purchase_line_id.is_deposit and line.quantity > 0
                )
            )

    def _adjust_journal_item_balances_for_deposit(self):
        """Reconcile deposit and stock received balances when the move currency
        differs from the company currency by resetting deposit lines to the
        original deposit bill amount and redistributing the difference over
        non-deposit product lines.
        """
        for rec in self:
            deposit_lines = rec.line_ids.filtered(
                lambda line: line.display_type == "product"
                and line.purchase_line_id.is_deposit
            )
            if not deposit_lines:
                continue
            amount_diff = 0.0
            for line in deposit_lines:
                balance = sum(
                    line.purchase_line_id.invoice_lines.filtered(
                        lambda l: l.move_id.state == "posted" and l.move_id.is_deposit
                    ).mapped("balance")
                )
                amount_diff += balance + line.balance
                line.with_context(skip_deposit_adjustment=True).balance = -1 * balance
            if not amount_diff:
                continue
            product_lines = rec.line_ids.filtered(
                lambda line: line.display_type == "product"
                and line.purchase_line_id
                and not line.purchase_line_id.is_deposit
            )
            if not product_lines:
                continue
            line_count = len(product_lines)
            total_balance = sum(product_lines.mapped("balance"))
            remaining = amount_diff
            for idx, line in enumerate(product_lines):
                if idx < line_count - 1:
                    if total_balance:
                        raw_share = amount_diff * (line.balance / total_balance)
                    else:
                        raw_share = amount_diff / line_count
                    share = rec.currency_id.round(raw_share)
                    remaining -= share
                else:
                    # last line gets whatever remains, to keep sums exact
                    share = rec.currency_id.round(remaining)
                line.with_context(skip_deposit_adjustment=True).balance = (
                    line.balance + share
                )

    # Expect to extend as necessary for other move types
    def _moves_needing_deposit_adjustment(self):
        return self.filtered(
            lambda m: (
                m.move_type == "in_invoice"
                and not m.is_deposit
                and m.line_ids.filtered(
                    lambda l: l.purchase_line_id and l.purchase_line_id.is_deposit
                )
            )
        )

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._moves_needing_deposit_adjustment()._adjust_journal_item_balances_for_deposit()
        return moves

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("skip_deposit_adjustment"):
            return res
        self._moves_needing_deposit_adjustment()._adjust_journal_item_balances_for_deposit()
        return res
