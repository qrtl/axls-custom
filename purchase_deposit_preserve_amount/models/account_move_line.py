# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _generate_price_difference_vals(self, layers):
        self.ensure_one()
        is_deposit_move = self.move_id.line_ids.filtered(
            lambda line: line.purchase_line_id.is_deposit
        )
        if not is_deposit_move:
            return super()._generate_price_difference_vals(layers)
        self = self.with_context(need_deposit_adj_aml=self)
        return super()._generate_price_difference_vals(layers)
