# Copyright 2024 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountAnalylticPlan(models.Model):
    _inherit = "account.analytic.plan"

    category_id = fields.Many2one("account.analytic.category")
