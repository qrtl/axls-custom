# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_confirm(self, merge=True, merge_into=False):
        # We particularly want to skip
        # https://github.com/OCA/OCB/blob/53e1941/addons/mrp/models/mrp_unbuild.py#L148
        # for component receipts to avoid generation of stock.move.line records with
        # the standard logic.
        if self._context.get("exact_unbuild") and self._context.get("produce_moves"):
            return self
        return super()._action_confirm(merge, merge_into)
