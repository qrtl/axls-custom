# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class IrModel(models.Model):
    _inherit = "ir.model"

    lot_index_column = fields.Char(
        help="Enter the field name used to identify the 'lot_id' during imports. "
        "This should be set to the field path where the lot information is stored, "
        "e.g., 'move_line_ids/lot_id'. This helps in concatenating the product "
        "name to the lot name to uniquely identify lots during imports."
    )

    product_index_column = fields.Char(
        help="Enter the field name used to identify the 'product_id' during imports. "
        "This should be set to the field path where the product information is stored, "
        "e.g., 'move_line_ids/product_id'. This is used to fetch the product name "
        "for concatenating it with the lot name during data conversion in imports."
    )
