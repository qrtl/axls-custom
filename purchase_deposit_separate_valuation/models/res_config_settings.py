# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sep_val_grni_adjustment_account_id = fields.Many2one(
        related="company_id.sep_val_grni_adjustment_account_id",
        readonly=False,
    )
    sep_val_grni_adjustment_journal_id = fields.Many2one(
        related="company_id.sep_val_grni_adjustment_journal_id",
        readonly=False,
    )
