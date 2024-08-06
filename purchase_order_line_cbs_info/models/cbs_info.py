# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class CBSINFO(models.Model):
    _name = "cbs.info"
    _description = "CBS Information"

    code = fields.Char(required=True)
    order_line_id = fields.Many2one(
        "purchase.order.line", ondelete="cascade", required=True
    )
    product_id = fields.Many2one(related="order_line_id.product_id", store=True)
    quantity = fields.Float()
    purchase_order_line_price = fields.Float(
        related="order_line_id.price_unit",
        string="Order Line Price Unit",
        digits="Product Price",
        readonly=True,
        store=True,
    )
    cbs_price_unit = fields.Float(string="CBS Price Unit", digits="Product Price")
    price_total = fields.Monetary(
        compute="_compute_price_total", string="Total", store=True
    )
    currency_id = fields.Many2one(
        related="order_line_id.currency_id", store=True, readonly=True
    )

    @api.depends("quantity", "cbs_price_unit")
    def _compute_price_total(self):
        for line in self:
            line.price_total = line.quantity * line.cbs_price_unit
