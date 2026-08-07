# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    ignore_last_purchase_date = fields.Boolean(
        compute="_compute_ignore_last_purchase_date",
        store=True,
        help="Ignore assigning last purchase date",
    )

    @api.depends("picking_id.ignore_last_purchase_date")
    def _compute_ignore_last_purchase_date(self):
        for move in self:
            move.ignore_last_purchase_date = move.picking_id.ignore_last_purchase_date
            move.product_id._compute_last_purchase_date()
