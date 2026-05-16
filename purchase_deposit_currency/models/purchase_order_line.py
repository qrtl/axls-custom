# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        readonly=True,
    )
    deposit_company_amount = fields.Monetary(
        string="Deposit Company-Currency Amount",
        currency_field="company_currency_id",
        copy=False,
        help="Company-currency value carried over from the deposit vendor "
        "bill. Used to populate ``company_amount`` on the negative "
        "deposit-offset line of the final invoice so the JPY amount "
        "matches what was actually paid.",
    )

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move=move)
        if self.is_deposit and self.deposit_company_amount:
            # purchase_deposit flips quantity to -1 for the offset line.
            # The corresponding company-currency value must also flip
            # so balance lands at -<deposit JPY> on the final invoice.
            res["company_amount"] = -self.deposit_company_amount
        return res
