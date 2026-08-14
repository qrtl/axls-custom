# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    company_amount = fields.Monetary(
        string="Company Currency Amount",
        currency_field="company_currency_id",
        help="Manually-entered company-currency value of this line. "
        "When set (non-zero), the line's balance is forced to this value, "
        "bypassing the standard amount_currency × exchange_rate "
        "calculation. Only available on vendor bills that are part of a "
        "purchase-deposit flow, where you actually paid an exact JPY amount "
        "that doesn't match today's exchange rate.",
    )
    company_amount_allowed = fields.Boolean(
        compute="_compute_company_amount_allowed",
        help="Technical field: True when this line belongs to a vendor bill "
        "that carries a purchase deposit, which is the only situation where "
        "a company_amount override is accepted.",
    )
    deposit_amount_adjusted = fields.Boolean(
        copy=False,
        help="Set automatically when this product line's company_amount was "
        "filled by the deposit rate-difference adjustment on the final "
        "invoice. Lets the value be recomputed when the rate changes without "
        "mistaking it for a manual override.",
    )

    def _is_company_amount_allowed(self):
        """The override only makes sense inside the ``purchase_deposit`` flow.

        Two cases qualify, and both are recognised by the presence of a
        deposit line on the move itself:

        * the deposit vendor bill — it holds the positive deposit line whose
          company-currency value the user wants to pin;
        * the final invoice — it holds the negative deposit-offset line, and
          its product lines absorb the deposit's rate difference.

        On any other vendor bill the standard ``amount_currency ×
        currency_rate`` conversion applies, unchanged.
        """
        self.ensure_one()
        if self.move_id.move_type not in ("in_invoice", "in_refund"):
            return False
        if self.display_type != "product":
            return False
        return bool(
            self.move_id.line_ids.filtered(
                lambda l: l.display_type == "product" and l.purchase_line_id.is_deposit
            )
        )

    @api.depends(
        "display_type",
        "move_id.move_type",
        "move_id.line_ids.display_type",
        "move_id.line_ids.purchase_line_id.is_deposit",
    )
    def _compute_company_amount_allowed(self):
        for line in self:
            line.company_amount_allowed = line._is_company_amount_allowed()

    @api.constrains("company_amount")
    def _check_company_amount_allowed(self):
        for line in self:
            if line.company_amount and not line._is_company_amount_allowed():
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
                        "move": line.move_id.display_name,
                    }
                )

    def _deposit_natural_balance(self):
        """Rate-based company-currency value of this line, i.e. what
        ``balance`` would be without any ``company_amount`` override. Used by
        the deposit rate-difference adjustment so its computation stays
        idempotent regardless of overrides already applied.
        """
        self.ensure_one()
        if not self.currency_rate:
            return self.balance
        return self.amount_currency / self.currency_rate

    @api.onchange("company_amount")
    def _onchange_company_amount(self):
        for line in self:
            if not line.company_amount:
                continue
            line._apply_company_amount_override()

    def _apply_company_amount_override(self):
        """Force the line's balance to ``company_amount`` with the sign that
        matches the line's intended direction. The companion AP / receivable
        line is auto-balanced by Odoo from the sum of the other lines.
        """
        self.ensure_one()
        if not self.company_amount or not self._is_company_amount_allowed():
            return
        rounding = self.company_currency_id.rounding
        amount_currency_positive = self.amount_currency >= 0
        target = abs(self.company_amount)
        signed_balance = target if amount_currency_positive else -target
        if float_is_zero(self.balance - signed_balance, precision_rounding=rounding):
            return
        self.balance = signed_balance

    def write(self, vals):
        res = super().write(vals)
        if (
            "company_amount" in vals
            or "amount_currency" in vals
            or "price_unit" in vals
            or "quantity" in vals
        ):
            for line in self.filtered("company_amount"):
                line._apply_company_amount_override()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines.filtered("company_amount"):
            line._apply_company_amount_override()
        return lines

    def _get_gross_unit_price(self):
        # Make purchase_stock's price-diff logic (which divides by currency_rate)
        # see the company_amount override, so SVL/AML adjustments are generated.
        res = super()._get_gross_unit_price()
        if (
            self.company_amount
            and self.quantity
            and self.currency_rate
            and self.currency_id != self.company_currency_id
            and self._is_company_amount_allowed()
        ):
            sign = -1 if self.move_id.move_type == "in_refund" else 1
            return abs(self.company_amount) / self.quantity * self.currency_rate * sign
        return res
