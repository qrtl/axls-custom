# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_deposit = fields.Boolean(
        string="Is a Deposit Bill",
        compute="_compute_is_deposit",
        help="Technical field: this bill was raised by the Register Deposit "
        "wizard, i.e. it books a deposit rather than netting one off. It is "
        "the only kind of bill on which the company-currency amount can be "
        "entered by hand.",
    )

    @api.depends(
        "invoice_line_ids.purchase_line_id.is_deposit",
        "invoice_line_ids.quantity",
    )
    def _compute_is_deposit(self):
        """A deposit bill books the deposit with a positive quantity. The final
        bill reuses the same deposit purchase order line for its offset, but
        with a negative one, so the sign is what tells the two apart.
        """
        for move in self:
            move.is_deposit = bool(
                move.invoice_line_ids.filtered(
                    lambda l: l.purchase_line_id.is_deposit and l.quantity > 0
                )
            )

    def _get_deposit_offset_lines(self):
        """The negative-quantity deposit lines ``purchase_deposit`` adds to the
        final vendor bill to net off a deposit already billed.
        """
        self.ensure_one()
        return self.line_ids.filtered(
            lambda l: l.display_type == "product"
            and l.purchase_line_id.is_deposit
            and l.quantity < 0
        )

    def _get_company_amount_targets(self):
        """Company-currency balance every overridden line of this move should
        end up with, as ``{line: balance}``. Lines absent from the result keep
        the standard rate-based conversion.

        Three sources, in precedence order:

        1. a manual ``company_amount`` -- the amount the user says was paid;
        2. a deposit-offset line, pinned to what the deposit really cost, so
           the deposit account closes out at the amount actually paid however
           the rate has moved since;
        3. the resulting rate difference, absorbed by the product lines.

        (3) is the accounting policy this module exists for: a paid deposit is
        non-monetary, so the goods are measured at the deposit's own rate for
        the prepaid slice and at the current rate for the rest. The difference
        therefore belongs in the acquisition cost, not in an FX gain or loss.
        Product lines the user has priced by hand are left out of it -- a
        manual value is never overwritten.
        """
        self.ensure_one()
        company_currency = self.company_id.currency_id
        if self.currency_id == company_currency:
            return {}
        product_lines = self.line_ids.filtered(lambda l: l.display_type == "product")
        if not product_lines.filtered(lambda l: l.purchase_line_id.is_deposit):
            return {}
        targets = {}
        for line in product_lines.filtered("company_amount"):
            # Entered unsigned; the debit/credit direction is the line's own.
            sign = -1 if line.amount_currency < 0 else 1
            targets[line] = sign * abs(line.company_amount)
        offset_lines = self._get_deposit_offset_lines()
        for line in offset_lines:
            deposit_amount = line.purchase_line_id.deposit_company_amount
            if line in targets or company_currency.is_zero(deposit_amount):
                continue
            targets[line] = -deposit_amount
        delta = sum(
            line._get_rate_based_balance() - targets[line]
            for line in offset_lines
            if line in targets
        )
        # Goods lines never carry a value the user typed -- only the deposit
        # line may be pinned by hand -- so they all absorb.
        absorbing_lines = product_lines.filtered(
            lambda l: l.purchase_line_id and not l.purchase_line_id.is_deposit
        )
        if company_currency.is_zero(delta) or not absorbing_lines:
            return targets
        weights = {
            line: abs(line._get_rate_based_balance()) for line in absorbing_lines
        }
        total_weight = sum(weights.values())
        remaining = delta
        for idx, line in enumerate(absorbing_lines):
            if idx < len(absorbing_lines) - 1:
                if total_weight:
                    share = company_currency.round(delta * weights[line] / total_weight)
                else:
                    share = company_currency.round(delta / len(absorbing_lines))
                remaining -= share
            else:
                # The last line takes the rounding remainder, so the shares add
                # back up to the delta exactly and the move stays balanced.
                share = company_currency.round(remaining)
            targets[line] = company_currency.round(
                line._get_rate_based_balance() + share
            )
        return targets

    def _rebalance_payment_term_lines(self):
        """Absorb any leftover imbalance into the payment-term line(s).

        Odoo normally rebuilds the payable from ``needed_terms`` whenever the
        lines move, but that sync only fires when the *needed* values change.
        Pinning a balance does not always change them: editing the bill date
        moves ``currency_rate``, so the standard invoice sync re-derives every
        line's balance from the new rate -- payable included -- while the
        overridden lines are put straight back where they were. The needed
        totals come out identical, the sync concludes there is nothing to do,
        and the payable keeps its rate-converted value. The move is then saved
        unbalanced.

        That bites precisely when the override makes the move's total blind to
        the rate. On the deposit bill it does: the one non-payable line is
        pinned to the amount paid, so the needed total is the same before and
        after. The final bill is not affected -- its goods line is rate-based
        plus the deposit's rate difference, so the total does move and Odoo's
        own sync notices and rewrites the payable.

        So rather than trying to provoke that sync, enforce the invariant it
        would have enforced. When the payment-term line does not exist yet --
        during creation -- there is nothing to correct here and the standard
        sync builds it from the overridden balances anyway.
        """
        self.ensure_one()
        company_currency = self.company_id.currency_id
        term_lines = self.line_ids.filtered(lambda l: l.display_type == "payment_term")
        if not term_lines:
            return
        imbalance = company_currency.round(sum(self.line_ids.mapped("balance")))
        if company_currency.is_zero(imbalance):
            return
        weights = {line: abs(line.balance) for line in term_lines}
        total_weight = sum(weights.values())
        remaining = imbalance
        for idx, line in enumerate(term_lines):
            if idx < len(term_lines) - 1:
                if total_weight:
                    share = company_currency.round(
                        imbalance * weights[line] / total_weight
                    )
                else:
                    share = company_currency.round(imbalance / len(term_lines))
                remaining -= share
            else:
                # The last line takes the rounding remainder, so the move comes
                # out balanced to the cent.
                share = company_currency.round(remaining)
            line.balance = company_currency.round(line.balance - share)

    def _apply_company_amount_overrides(self):
        for move in self:
            if move.move_type not in ("in_invoice", "in_refund"):
                continue
            company_currency = move.company_id.currency_id
            targets = move._get_company_amount_targets()
            if not targets:
                continue
            for line, target in targets.items():
                if not company_currency.is_zero(line.balance - target):
                    line.balance = target
            move._rebalance_payment_term_lines()
