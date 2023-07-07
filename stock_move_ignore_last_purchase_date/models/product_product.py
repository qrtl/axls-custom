# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _assign_last_purchase_date(self, move):
        if move.ignore_last_purchase_date:
            return False
        return super()._assign_last_purchase_date(move)
