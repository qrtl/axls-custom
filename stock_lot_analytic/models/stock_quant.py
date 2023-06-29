# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockQuant(models.Model):
    _name = "stock.quant"
    _inherit = ["stock.quant", "analytic.mixin"]

    analytic_distribution = fields.Json(related="lot_id.analytic_distribution")

    @api.model
    def _get_inventory_fields_create(self):
        fields = super()._get_inventory_fields_create()
        fields += ["analytic_distribution", "analytic_precision"]
        return fields
