# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _apply_price_difference(self):
        """Suppress price-difference SVL creation for vendor bills linked to
        a separate-valuation purchase order, so stock value stays at the
        receipt cost regardless of the billed amount.
        """

        def _is_separate(line):
            purchase = (
                line.purchase_line_id.order_id or line.move_id.purchase_id
            )
            return bool(purchase and purchase.use_separate_valuation)

        separate = self.filtered(_is_separate)
        regular = self - separate
        if not regular:
            return (
                self.env["stock.valuation.layer"].sudo(),
                self.env["account.move.line"].sudo(),
            )
        return super(AccountMoveLine, regular)._apply_price_difference()
