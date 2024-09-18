# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    budget_line_ids = fields.One2many(
        "purchase.budget.line",
        "order_line_id",
        copy=False,
    )
    budget_qty = fields.Float(
        string="Budget Quantity",
        digits="Product Unit of Measure",
        compute="_compute_budget_qty",
    )
    budget_code_ids = fields.Many2many(
        "budget.code",
        compute="_compute_budget_code_ids",
        store=True,
    )
    quick_encoding_budget_qty = fields.Binary(
        compute="_compute_quick_encoding_budget_qty",
        exportable=False,
    )

    @api.depends("budget_line_ids.quantity")
    def _compute_budget_qty(self):
        for line in self:
            line.budget_qty = sum(line.budget_line_ids.mapped("quantity"))

    @api.depends("budget_line_ids.budget_code_id")
    def _compute_budget_code_ids(self):
        for line in self:
            line.budget_code_ids = line.budget_line_ids.budget_code_id

    @api.depends("product_qty", "budget_qty")
    def _compute_quick_encoding_budget_qty(self):
        for line in self:
            line.quick_encoding_budget_qty = line.product_qty - line.budget_qty

    def action_show_budget_lines(self):
        self.ensure_one()
        view = self.env.ref(
            "purchase_budget_line.view_purchase_order_line_budget_line_form"
        )
        return {
            "name": _("Purchase Budget Lines"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "purchase.order.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
        }
