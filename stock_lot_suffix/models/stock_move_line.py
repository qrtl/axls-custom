# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _set_lot_suffix(self):
        lots = self.lot_id
        if not lots:
            return
        update_values = {}
        if self.move_id.picking_id.purchase_id.channel_category:
            update_values[
                "channel_category"
            ] = self.move_id.picking_id.purchase_id.channel_category
        if self.move_id.picking_id.purchase_id.analytic_account_ids:
            names = []
            for ad in self.move_id.picking_id.purchase_id.analytic_account_ids:
                if ad.lot_suffix:
                    names.append(ad.lot_suffix)
            if names:
                update_values["lot_suffix"] = "-".join(names)
        lots.write(update_values)

    def _action_done(self):
        self._set_lot_suffix()
        return super()._action_done()
