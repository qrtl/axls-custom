# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _assign_last_purchase_date(self, move):
        last_purchase_date = super()._assign_last_purchase_date(move)
        if move.ignore_last_purchase_date and self.man_last_purchase_date:
            last_purchase_date = self.man_last_purchase_date
        return last_purchase_date
