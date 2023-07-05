# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    ignore_last_purchase_date = fields.Boolean(
        related="picking_id.ignore_last_purchase_date", store=True
    )
