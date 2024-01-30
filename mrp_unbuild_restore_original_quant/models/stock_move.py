# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_confirm(self, merge=True, merge_into=False):
        if self.env.context.get("exact_unbuild") and self.env.context.get(
            "produce_move"
        ):
            return self
        return super(StockMove, self)._action_confirm(merge, merge_into)
