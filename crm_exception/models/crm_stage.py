# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class CrmStage(models.Model):
    _inherit = "crm.stage"

    exception_ids = fields.Many2many("exception.rule", domain="[('model', '=', 'crm.lead')]")