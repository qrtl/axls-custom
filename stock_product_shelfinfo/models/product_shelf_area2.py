# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductShelfArea2(models.Model):
    _name = "product.shelf.area2"
    _description = "Product Shelf Area 2"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
