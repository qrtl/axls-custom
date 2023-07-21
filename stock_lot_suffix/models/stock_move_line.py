# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        res = super()._action_done()
        for ml in self:
            if not ml.lot_id:
                continue
            vals = {}
            purchase_line = ml.move_id.purchase_line_id
            vals["channel_category"] = purchase_line.order_id.channel_category
            # We assume that there is only one analytic account with lot_suffix if any.
            analytic_account = purchase_line.analytic_account_ids.filtered(
                lambda x: x.lot_suffix
            )
            if analytic_account:
                vals["lot_suffix"] = analytic_account[0].lot_suffix
            # lot_suffixes = [
            #     suffix
            #     for suffix in purchase_line.analytic_account_ids.mapped("lot_suffix")
            #     if suffix
            # ]
            # vals["lot_suffix"] = lot_suffixes[0] if lot_suffixes else None
            ml.lot_id.write(vals)
        return res
