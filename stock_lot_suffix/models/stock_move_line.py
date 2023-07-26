# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        res = super()._action_done()
        # Use exists() to ensure that we only work with records
        # that are currently present in the database.
        # This is because the super call "_action_done()" may delete some of the records.
        # This avoids errors that would occur if we try to operate on deleted records.
        self = self.exists()
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
            ml.lot_id.write(vals)
        return res
