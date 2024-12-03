# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    acceptance_tester_id = fields.Many2one(
        "res.partner", domain=[("is_acceptance_tester", "=", True)]
    )
    need_acceptance_test = fields.Boolean(compute="_compute_need_acceptance_test")

    def _compute_need_acceptance_test(self):
        for order in self:
            order.need_acceptance_test = False
            if order.order_line.filtered(
                lambda x: x.product_id
                and x.product_type != "service"
                and x.qty_received != x.product_qty
            ):
                order.need_acceptance_test = True
