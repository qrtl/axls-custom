# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    price_discrepancy_threshold_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Value'),
        ('ignore', 'Ignore')
        ], string="Global Price Discrepancy Threshold Type",
        default='ignore'
    )

    price_discrepancy_threshold_value = fields.Float(
        string="Global Threshold Value",
        help="Global threshold value for price discrepancy warnings."
    )
