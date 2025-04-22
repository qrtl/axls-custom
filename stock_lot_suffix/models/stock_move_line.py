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
            purchase_line = ml.move_id.purchase_line_id
            ml.lot_id.write(
                {"channel_category": purchase_line.order_id.channel_category}
            )
        return res
