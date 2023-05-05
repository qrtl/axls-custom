# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductShelfInfoArea(models.Model):
    _name = "product.shelfinfo_area"
    _description = "Product Shelfinfo Area"

    name = fields.Char(required=True)
    type = fields.Selection(
        [("area1", "Area 1"), ("area2", "Area 2"), ("position", "Position")],
        required=True,
    )
