# -*- coding: utf-8 -*-
from odoo import models

_VENDOR_BILL_TYPES = frozenset({'in_invoice', 'in_refund', 'in_receipt'})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _apply_price_difference(self):
        """Block price-difference SVL creation for separate-valuation vendor bills."""
        def _is_separate(line):
            if line.move_id.move_type not in _VENDOR_BILL_TYPES:
                return False
            purchase = line.purchase_line_id.order_id or line.move_id.purchase_id
            return bool(purchase and purchase.use_separate_valuation)

        separate = self.filtered(_is_separate)
        non_separate = self - separate
        if not non_separate:
            return self.env['stock.valuation.layer'], self.env['account.move.line']
        return super(AccountMoveLine, non_separate)._apply_price_difference()
