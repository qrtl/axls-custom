# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductShelfPosition(models.Model):
    _name = "product.shelf.position"
    _description = "Product Shelf Position"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
