# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models

_VENDOR_BILL_TYPES = frozenset({"in_invoice", "in_refund", "in_receipt"})


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        self._trigger_sep_val_grni_sync(posted)
        return posted

    def button_draft(self):
        result = super().button_draft()
        self._trigger_sep_val_grni_sync(self)
        return result

    def button_cancel(self):
        result = super().button_cancel()
        self._trigger_sep_val_grni_sync(self)
        return result

    def _trigger_sep_val_grni_sync(self, moves):
        purchases = self.env["purchase.order"]
        for move in moves.filtered(lambda m: m.move_type in _VENDOR_BILL_TYPES):
            purchases |= move._get_sep_val_purchase_orders()
        if purchases:
            purchases._sync_sep_val_grni_adjustment()

    def _get_sep_val_purchase_orders(self):
        self.ensure_one()
        candidates = self.purchase_id | self.invoice_line_ids.mapped(
            "purchase_line_id.order_id"
        )
        return candidates.filtered("use_separate_valuation")
