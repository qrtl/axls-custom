# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains(
        "move_type",
        "line_ids",
        "line_ids.company_amount",
        "line_ids.display_type",
        "line_ids.purchase_line_id",
    )
    def _check_company_amount_allowed(self):
        """Guard the override's scope from the move, not from the line.

        The rule reads the whole move -- its type and whether any of its lines
        is a deposit line -- so it has to be constrained on the move's fields.
        Hung off ``account.move.line.company_amount`` alone it would only fire
        when that one field is written, and removing the deposit line from a
        bill that already carries overrides would slip through untouched,
        leaving the move forcing balances it is no longer entitled to.
        """
        for move in self:
            for line in move.line_ids.filtered("company_amount"):
                if line._is_company_amount_allowed():
                    continue
                raise ValidationError(
                    _(
                        "'%(field)s' can only be set on a vendor bill that "
                        "carries a purchase deposit. On line '%(line)s' of "
                        "'%(move)s' the standard exchange-rate conversion "
                        "applies; clear the value to continue."
                    )
                    % {
                        "field": line._fields["company_amount"].string,
                        "line": line.name or line.product_id.display_name or "/",
                        "move": move.display_name,
                    }
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
        absorbing_lines = product_lines.filtered(
            lambda l: not l.company_amount
            and l.purchase_line_id
            and not l.purchase_line_id.is_deposit
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

    def _apply_company_amount_overrides(self):
        for move in self:
            if move.move_type not in ("in_invoice", "in_refund"):
                continue
            company_currency = move.company_id.currency_id
            for line, target in move._get_company_amount_targets().items():
                if not company_currency.is_zero(line.balance - target):
                    line.balance = target
