# Copyright 2023 Quartile Limited

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_via_plm = fields.Boolean(readonly=True)
