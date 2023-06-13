# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockQuant(models.Model):
    _name = "stock.quant"
    _inherit = ["stock.quant", "analytic.mixin"]

    analytic_distribution = fields.Json(related="lot_id.analytic_distribution")
