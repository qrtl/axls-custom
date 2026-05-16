# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

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
