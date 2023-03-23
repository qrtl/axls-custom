# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    shelfinfo_ids = fields.One2many(
        "product.shelfinfo",
        "product_id",
        string="Shelf Information",
    )
