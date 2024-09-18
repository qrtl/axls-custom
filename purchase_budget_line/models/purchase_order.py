# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    budget_qty_inconsistency_warning = fields.Text(
        compute="_compute_budget_qty_inconsistency_warning",
    )
    budget_code_ids = fields.Many2many(related="order_line.budget_code_ids")

    @api.constrains("order_line.product_qty", "order_line.budget_qty")
    def _compute_budget_qty_inconsistency_warning(self):
        for order in self:
            message = False
            product_names = ""
            for line in order.order_line:
                if not line.budget_line_ids or line.budget_qty == line.product_qty:
                    continue
                product_names += "\n" + line.product_id.display_name
            if product_names:
                message = _(
                    "There is a line with inconsistent quantities between order and "
                    "budget:\n%s",
                    product_names,
                )
            order.budget_qty_inconsistency_warning = message
