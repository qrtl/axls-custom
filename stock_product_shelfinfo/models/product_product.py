# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    shelfinfo_ids = fields.One2many(
        "product.shelfinfo",
        "product_id",
        string="Shelf Information",
    )
