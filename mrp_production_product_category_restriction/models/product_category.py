# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    produce_ok = fields.Boolean(
        "Can be Manufactured",
        help="If disabled, products with this category will be disallowed to be "
        "manufactured.",
    )
