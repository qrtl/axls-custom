# Copyright 2025 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_unarchive(self):
        res = super().action_unarchive()
        self.filtered(lambda p: p.is_draft).write({"is_draft": False})
        return res
