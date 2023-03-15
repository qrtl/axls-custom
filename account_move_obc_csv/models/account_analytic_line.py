# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAnalylticLine(models.Model):
    _inherit = "account.analytic.line"

    plan_type = fields.Selection(related="plan_id.plan_type", store=True)
