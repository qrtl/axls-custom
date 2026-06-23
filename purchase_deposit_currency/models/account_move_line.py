# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    company_amount = fields.Monetary(
        string="Company Currency Amount",
        currency_field="company_currency_id",
        help="Manually-entered company-currency value of this line. "
        "When set (non-zero), the line's balance is forced to this value, "
        "bypassing the standard amount_currency × exchange_rate "
        "calculation. Useful for foreign-currency vendor bills where you "
        "actually paid an exact JPY amount that doesn't match today's "
        "exchange rate.",
    )
    deposit_amount_adjusted = fields.Boolean(
        copy=False,
        help="Set automatically when this product line's company_amount was "
        "filled by the deposit rate-difference adjustment on the final "
        "invoice. Lets the value be recomputed when the rate changes without "
        "mistaking it for a manual override.",
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
        if not self.company_amount:
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
            and self.move_id.move_type in ("in_invoice", "in_refund")
        ):
            sign = -1 if self.move_id.move_type == "in_refund" else 1
            return abs(self.company_amount) / self.quantity * self.currency_rate * sign
        return res
