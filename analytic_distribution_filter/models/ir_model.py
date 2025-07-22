# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrModel(models.Model):
    _inherit = "ir.model"

    apply_analytic_distribution_filter = fields.Boolean(
        help="Enable to apply the analytic distribution filter on this model."
    )
