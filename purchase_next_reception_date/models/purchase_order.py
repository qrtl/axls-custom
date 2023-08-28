# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    next_reception_date = fields.Datetime(
        compute="_compute_next_reception_date", store=True
    )

    @api.depends(
        "order_line.product_id",
        "order_line.product_qty",
        "order_line.qty_received",
        "order_line.qty_invoiced",
        "order_line.date_planned",
    )
    def _compute_next_reception_date(self):
        for order in self:
            lines = order.order_line.filtered(
                lambda x: (
                    (
                        x.product_id.detailed_type != "service"
                        and x.qty_received < x.product_qty
                    )
                    or (
                        x.product_id.detailed_type == "service"
                        and x.qty_invoiced < x.product_qty
                    )
                )
            )
            dates = lines.mapped("date_planned")
            order.next_reception_date = min(dates) if dates else False
