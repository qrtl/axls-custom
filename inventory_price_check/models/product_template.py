# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    price_discrepancy_threshold_type = fields.Selection(
        [("percentage", "Percentage"), ("fixed", "Fixed Value"), ("ignore", "Ignore")]
    )
    price_discrepancy_threshold_value = fields.Float(
        help="Threshold value for price discrepancy warnings."
    )
