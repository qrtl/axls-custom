# Copyright 2024 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountAnalylticPlan(models.Model):
    _inherit = "account.analytic.plan"

    code = fields.Char()
