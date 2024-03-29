# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.product"

    man_last_purchase_date = fields.Date(
        "Last Purchase Date (Man.)",
        copy=False,
        help="Update this field to force set Last Purchase Date in absence of past "
        "receipt records. If there is a receipt record dated after this date, the date "
        "of the receipt prevails.",
    )
    last_purchase_date = fields.Date(
        compute="_compute_last_purchase_date",
        store=True,
        help="Date of the last receipt from the supplier.",
    )

    @api.depends("stock_move_ids.state", "man_last_purchase_date")
    def _compute_last_purchase_date(self):
        for product in self:
            last_purchase_date = False
            man_last_purchase_date = product.man_last_purchase_date
            move = self.env["stock.move"].search(
                self._get_move_domain(product), order="id desc", limit=1
            )
            if move:
                last_purchase_date = fields.Date.context_today(self, move.date)
            if (
                not last_purchase_date
                or man_last_purchase_date
                and man_last_purchase_date > last_purchase_date
            ):
                last_purchase_date = man_last_purchase_date
            product.last_purchase_date = last_purchase_date
            product.product_tmpl_id._compute_last_purchase_date()

    def _get_move_domain(self, product):
        return [
            ("product_id", "=", product.id),
            ("state", "=", "done"),
            ("picking_code", "=", "incoming"),
        ]
