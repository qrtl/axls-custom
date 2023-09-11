# Copyright 2023 Quartile Limited

from odoo import fields, models


class PlmProcureFlag(models.Model):
    _name = "plm.procure.flag"
    _description = "PLM Procure Flag"
    _order = "name"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company")
    active = fields.Boolean(default=True)
