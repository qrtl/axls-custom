# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_domain(self, product):
        domain = super()._get_domain(product)
        domain = expression.AND([domain, [("ignore_last_purchase_date", "=", False)]])
        return domain
