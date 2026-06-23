# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _moves_needing_deposit_company_adjustment(self):
        return self.filtered(
            lambda m: m.move_type in ("in_invoice", "in_refund")
            and m.currency_id != m.company_id.currency_id
            and m.line_ids.filtered(
                lambda l: l.display_type == "product"
                and l.purchase_line_id.is_deposit
                and l.purchase_line_id.deposit_company_amount
                and l.quantity < 0
            )
        )

    def _apply_deposit_company_adjustment(self):
        """Push the deposit's exchange-rate difference onto the product
        line(s) of the final invoice.

        The deposit-offset line's company-currency balance is pinned to the
        JPY actually paid (``deposit_company_amount``), while the product
        lines are booked at the current rate. The gap between the deposit
        valued at the current rate and the JPY actually paid is the
        rate-difference; it belongs in the goods' acquisition cost. We absorb
        it into the product lines' ``company_amount`` so the goods value (and
        SVL) reflects the true cost and the auto-balanced payable equals the
        remaining foreign amount at the current rate.
        """
        for move in self:
            company_currency = move.company_id.currency_id
            offset_lines = move.line_ids.filtered(
                lambda l: l.display_type == "product"
                and l.purchase_line_id.is_deposit
                and l.purchase_line_id.deposit_company_amount
                and l.quantity < 0
            )
            # delta = deposit-at-current-rate - JPY actually paid (pinned
            # balance). Signed, so it works for in_invoice and in_refund.
            total_delta = sum(
                offset._deposit_natural_balance() - offset.balance
                for offset in offset_lines
            )
            if company_currency.is_zero(total_delta):
                continue
            product_lines = move.line_ids.filtered(
                lambda l: l.display_type == "product"
                and l.purchase_line_id
                and not l.purchase_line_id.is_deposit
                # Auto-fill empty lines and lines we filled before (rate may
                # have changed); never clobber a manual override.
                and (not l.company_amount or l.deposit_amount_adjusted)
            )
            if not product_lines:
                continue
            naturals = {l.id: l._deposit_natural_balance() for l in product_lines}
            total_weight = sum(abs(v) for v in naturals.values())
            line_count = len(product_lines)
            remaining = total_delta
            for idx, line in enumerate(product_lines):
                if idx < line_count - 1:
                    if total_weight:
                        weight = abs(naturals[line.id]) / total_weight
                        raw_share = total_delta * weight
                    else:
                        raw_share = total_delta / line_count
                    share = company_currency.round(raw_share)
                    remaining -= share
                else:
                    # last line absorbs the rounding remainder
                    share = company_currency.round(remaining)
                target = company_currency.round(naturals[line.id] + share)
                line.with_context(skip_deposit_company_adjustment=True).write(
                    {"company_amount": target, "deposit_amount_adjusted": True}
                )

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        target = moves._moves_needing_deposit_company_adjustment()
        target._apply_deposit_company_adjustment()
        return moves

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("skip_deposit_company_adjustment"):
            target = self._moves_needing_deposit_company_adjustment()
            target._apply_deposit_company_adjustment()
        return res

    def action_post(self):
        """When a deposit vendor bill is posted, capture the company-currency
        value of its deposit line and store it on the linked PO deposit
        line. The standard purchase_deposit offset on the final invoice then
        re-applies that value (see
        ``purchase.order.line._prepare_account_move_line``).
        """
        deposit_writes = []
        for move in self:
            for line in move.line_ids:
                po_line = line.purchase_line_id
                if not po_line or not po_line.is_deposit:
                    continue
                amount = line.company_amount or abs(line.balance)
                if amount:
                    deposit_writes.append((po_line, amount))
        res = super().action_post()
        for po_line, amount in deposit_writes:
            po_line.deposit_company_amount = amount
        return res
