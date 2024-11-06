# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    quality_check_categ_id = fields.Many2one(
        "quality.check.category",
        string="Quality Check Category",
        help="Selected category will show in the incoming receipt form (in the "
        "'Operations' tab) for information purpose.",
    )
