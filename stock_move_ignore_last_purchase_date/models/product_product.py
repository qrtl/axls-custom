# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _assign_last_purchase_date(self, move):
        if move.ignore_last_purchase_date:
            new_move = self.stock_move_ids.filtered(
                lambda m: m.state == "done"
                and m.picking_code == "incoming"
                and not m.ignore_last_purchase_date
            ).sorted(key=lambda m: m.id, reverse=True)[:1]
            if new_move:
                move_date = fields.Date.context_today(self, new_move.date)
                if move_date > self.man_last_purchase_date:
                    return move_date
                else:
                    return self.man_last_purchase_date
            else:
                return False
        return super()._assign_last_purchase_date(move)
