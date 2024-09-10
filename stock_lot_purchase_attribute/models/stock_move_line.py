# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    purchase_id = fields.Many2one(related="lot_id.purchase_id", store=True)
    purchase_partner_id = fields.Many2one(
        related="lot_id.purchase_partner_id", store=True
    )

    @api.model
    def _cron_update_stock_lot_purchase_information(self):
        move_lines = self.sudo().search(
            [
                ("move_id.purchase_line_id", "!=", False),
                ("lot_id", "!=", False),
                ("lot_id.purchase_id", "=", False),
            ]
        )
        for line in move_lines:
            line.lot_id.purchase_id = line.move_id.purchase_line_id.order_id.id
            line.lot_id.purchase_partner_id = (
                line.move_id.purchase_line_id.partner_id.id
            )
