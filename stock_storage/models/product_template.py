# Copyright 2022 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    storage_ids = fields.Many2many("stock.storage", domain=lambda self: [('product_id', '=', self.id)])