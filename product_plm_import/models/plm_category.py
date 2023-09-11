# Copyright 2023 Quartile Limited

from odoo import fields, models


class PlmCategory(models.Model):
    _name = "plm.category"
    _description = "PLM Category"
    _order = "name"

    name = fields.Char(
        required=True,
        help="Accepts wildcard matching. E.g. `*` matches any string, `?` matches any "
        "single character.",
    )
    company_id = fields.Many2one("res.company")
    active = fields.Boolean(default=True)
