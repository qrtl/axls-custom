# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    next_reception_date = fields.Date(
        compute="_compute_next_reception_date", store=True
    )

    @api.depends(
        "order_line.date_planned",
        "order_line.product_qty",
        "order_line.qty_received",
        "order_line.qty_invoiced",
    )
    def _compute_next_reception_date(self):
        for order in self:
            dates = order.order_line.filtered(
                lambda line: (
                    (
                        line.product_id.detailed_type != "service"
                        and line.qty_received < line.product_qty
                    )
                    or (
                        line.product_id.detailed_type == "service"
                        and line.qty_invoiced < line.product_qty
                    )
                )
            ).mapped("date_planned")

            order.next_reception_date = min(dates) if dates else False
