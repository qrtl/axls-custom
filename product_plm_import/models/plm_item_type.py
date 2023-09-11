# Copyright 2023 Quartile Limited

from odoo import fields, models


class PlmItemType(models.Model):
    _name = "plm.item.type"
    _description = "PLM Item Type"
    _order = "name"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company")
    active = fields.Boolean(default=True)
