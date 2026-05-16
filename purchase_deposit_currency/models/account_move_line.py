# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_deposit_line = fields.Boolean(
        related="purchase_line_id.is_deposit",
        store=True,
        string="Is Deposit Line",
        help="True when this account move line is the deposit (or deposit "
        "offset) line for a purchase order. The Company Currency Amount "
        "override is only honoured on deposit lines.",
    )
    company_amount = fields.Monetary(
        string="Company Currency Amount",
        currency_field="company_currency_id",
        help="Manually-entered company-currency value of this line. "
        "When set on a deposit line (non-zero), the line's balance is "
        "forced to this value, bypassing the standard amount_currency × "
        "exchange_rate calculation. Useful for foreign-currency deposits "
        "where you actually paid an exact JPY amount that doesn't match "
        "today's exchange rate. Ignored on non-deposit lines.",
    )

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

        Defence-in-depth: the override is only honoured on deposit lines
        (``is_deposit_line``); on any other line the value is ignored.
        """
        self.ensure_one()
        if not self.company_amount:
            return
        if not self.is_deposit_line:
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
