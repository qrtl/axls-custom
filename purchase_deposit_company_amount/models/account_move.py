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
    allow_company_amount = fields.Boolean(
        compute="_compute_allow_company_amount",
        help="Technical field: the company-currency amount may be entered by "
        "hand on this bill's deposit line.",
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

    @api.depends("is_deposit", "currency_id", "company_currency_id")
    def _compute_allow_company_amount(self):
        """A deposit bill kept in the company currency has nothing to override:
        its balance already *is* the amount paid, and
        ``_get_company_amount_targets`` skips the move entirely. Accepting a
        value there would silently do nothing, so the field is refused and its
        column hidden.
        """
        for move in self:
            move.allow_company_amount = bool(
                move.is_deposit and move.currency_id != move.company_currency_id
            )

    @api.constrains("currency_id", "line_ids")
    def _check_company_amount_allowed(self):
        """Odoo 16 ignores dotted paths in ``@api.constrains``, so the line-level
        check cannot see the bill turning ineligible under a value already
        entered -- switching the bill to the company currency, or the deposit
        line losing its positive quantity. Re-run it from the move.
        """
        self.line_ids._check_company_amount_allowed()

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

    def _get_absorbed_targets(self, absorbing_lines, delta):
        """Company-currency balance the goods lines should end up with once
        they have taken ``delta`` between them, as ``{line: balance}``, or
        ``{}`` when there is nothing to spread.
        """
        self.ensure_one()
        company_currency = self.company_id.currency_id
        if company_currency.is_zero(delta) or not absorbing_lines:
            return {}
        weights = {
            line: abs(line._get_rate_based_balance()) for line in absorbing_lines
        }
        total_weight = sum(weights.values())
        if not total_weight:
            # Nothing to prorate against. Unreachable through the wizard, since
            # goods worth nothing give a percentage deposit of nothing and so no
            # difference to spread, but the division below needs the guard; the
            # payment-term rebalance keeps the move balanced either way.
            return {}
        targets = {}
        remaining = delta
        last_line = absorbing_lines[-1]
        for line in absorbing_lines:
            if line == last_line:
                # The last line takes the rounding remainder, so the shares add
                # back up to the delta exactly and the move stays balanced.
                share = company_currency.round(remaining)
            else:
                share = company_currency.round(delta * weights[line] / total_weight)
                remaining -= share
            targets[line] = company_currency.round(
                line._get_rate_based_balance() + share
            )
        return targets

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
            # The offset credits the deposit account on a bill and debits it
            # back on a refund. _reverse_moves sign-flips neither the quantity
            # nor purchase_line_id, so the reversal of a final bill still
            # arrives here as an offset line, only pointing the other way -- a
            # fixed negative would credit the deposit a second time instead of
            # reinstating it. The direction is taken from the line rather than
            # from move_type because move_type flips the moment the reversal is
            # created, while amount_currency is still mid-sync; balance has to
            # agree in sign with amount_currency as it stands right now, which
            # is what account_move_line_check_amount_currency_balance_sign
            # enforces, and what makes the override safe to re-run.
            sign = -1 if line.amount_currency < 0 else 1
            targets[line] = sign * abs(deposit_amount)
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
        targets.update(self._get_absorbed_targets(absorbing_lines, delta))
        # Every remaining line this module governs goes back to the standard
        # conversion. Odoo will not do it: its own sync recomputes balance only
        # when amount_currency, currency_rate or move_type changes, and clearing
        # a pinned amount changes none of the three -- so without this the
        # override the module wrote would simply stay behind, and the bill would
        # keep quoting a figure nobody stands behind any more.
        for line in product_lines:
            targets.setdefault(line, line._get_rate_based_balance())
        return targets

    def _rebalance_payment_term_lines(self):
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
                share = company_currency.round(remaining)
            line.balance = company_currency.round(line.balance - share)

    def _apply_company_amount_overrides(self):
        """Posted moves are left alone, as every sibling of this hook in
        ``account.move._sync_dynamic_lines`` does. The targets are derived from
        ``currency_rate``, which is *not* stored -- it is resolved from
        ``res.currency.rate`` on every read -- so correcting or back-filling a
        rate after the fact silently moves them. Without this guard the next
        write to touch the move's lines, reconciling a payment among them,
        would re-book a posted entry and push the difference onto the payable.
        """
        for move in self:
            if move.move_type not in ("in_invoice", "in_refund"):
                continue
            if move.state == "posted":
                continue
            company_currency = move.company_id.currency_id
            targets = move._get_company_amount_targets()
            if not targets:
                continue
            rewritten = overriding = False
            for line, target in targets.items():
                if not company_currency.is_zero(line.balance - target):
                    line.balance = target
                    rewritten = True
                if not company_currency.is_zero(
                    target - line._get_rate_based_balance()
                ):
                    overriding = True
            # Settle the payable while any target departs from the rate, and on
            # the pass that puts the last one back. It has to keep happening
            # rather than only when this pass wrote something: Odoo's own
            # payment-term sync runs after this hook and rebuilds the term line
            # from the rate, so the settlement has to be redone behind it.
            # Outside those two cases the module is only watching the move, and
            # rebalancing would push its transient imbalances -- taxes not yet
            # rebuilt, say -- onto the payable.
            if rewritten or overriding:
                move._rebalance_payment_term_lines()
