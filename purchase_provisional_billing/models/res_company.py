# Copyright 2025 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sep_val_variance_account_id = fields.Many2one(
        "account.account",
        string="Settlement Adjustment Account",
        help="Account used to absorb the difference between the Final Bill "
        "amount and the sum of paired credit notes when the Final Bill is "
        "settled against advance bills.",
    )
