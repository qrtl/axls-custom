# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sep_val_grni_adjustment_account_id = fields.Many2one(
        "account.account",
        string="Separate-Valuation GRNI Adjustment Account",
        help="Account that absorbs the residual on the Stock-Input (GRNI) "
        "account when a vendor bill amount differs from the receipt cost "
        "on a Separate-Valuation purchase order. Typically an expense / "
        "loss-gain account.",
    )
    sep_val_grni_adjustment_journal_id = fields.Many2one(
        "account.journal",
        string="Separate-Valuation GRNI Adjustment Journal",
        domain="[('type', '=', 'general')]",
        help="Journal used to post the GRNI adjustment entry. Defaults to "
        "the first General journal of the company if not configured.",
    )
