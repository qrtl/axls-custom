# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    obc_tax_category = fields.Char(
        "OBC Tax Category",
        help="The set value will be used in OBC data export.",
    )
    obc_tax_rate_type = fields.Selection(
        selection=[("0", "0: Standard"), ("1", "1: Reduced")],
        string="OBC Tax Rate Type",
        help="The set value will be used in OBC data export.",
    )
