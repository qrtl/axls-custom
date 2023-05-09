# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductShelfArea1(models.Model):
    _name = "product.shelf.area1"
    _description = "Product Shelf Area 1"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
