# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseBudgetLine(models.Model):
    _name = "purchase.budget.line"
    _description = "Purchase Budget Line"

    order_line_id = fields.Many2one(
        "purchase.order.line", ondelete="cascade", required=True
    )
    budget_code_id = fields.Many2one("budget.code", required=True)
    budget_ref = fields.Char()
    product_id = fields.Many2one(related="order_line_id.product_id", store=True)
    quantity = fields.Float()
    uom_id = fields.Many2one(related="order_line_id.product_uom", store=True)
    purchase_price_unit = fields.Float(
        related="order_line_id.price_unit",
        string="Purchase Unit Price",
        digits="Product Price",
        store=True,
    )
    budget_price_unit = fields.Float(digits="Product Price", string="Budget Unit Price")
    price_total = fields.Monetary(
        compute="_compute_price_total", string="Total", store=True
    )
    currency_id = fields.Many2one(related="order_line_id.currency_id", store=True)
    partner_id = fields.Many2one(related="order_line_id.partner_id", store=True)
    order_id = fields.Many2one(related="order_line_id.order_id", store=True)
    date_order = fields.Datetime(related="order_line_id.date_order", store=True)
    date_planned = fields.Datetime(related="order_line_id.date_planned", store=True)
    order_state = fields.Selection(
        related="order_line_id.state",
        string="Order Status",
        store=True,
    )
    invoice_ids = fields.Many2many(
        "account.move", compute="_compute_invoice_ids", string="Bills", store=True
    )

    @api.depends("quantity", "budget_price_unit")
    def _compute_price_total(self):
        for rec in self:
            rec.price_total = rec.quantity * rec.budget_price_unit

    @api.depends("order_line_id.invoice_lines")
    def _compute_invoice_line_ids(self):
        for rec in self:
            rec.invoice_line_ids = False
            if rec.order_line_id.invoice_lines:
                rec.invoice_line_ids = rec.order_line_id.invoice_lines

    @api.depends("order_line_id.invoice_lines.move_id")
    def _compute_invoice_ids(self):
        for rec in self:
            invoices = rec.order_line_id.invoice_lines.move_id
            rec.invoice_ids = invoices
