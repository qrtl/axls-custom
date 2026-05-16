# Copyright 2025 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sep_val_variance_account_id = fields.Many2one(
        related="company_id.sep_val_variance_account_id",
        readonly=False,
    )
