# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _set_channel_category(self):
        move_lines = self.env["stock.move.line"].search([("picking_id", "=", self.id)])
        lot_ids = move_lines.mapped("lot_id").ids
        if lot_ids:
            lots = self.env["stock.lot"].browse(lot_ids)
            update_values = {}
            if self.purchase_id.channel_category:
                update_values["channel_category"] = self.purchase_id.channel_category
            if self.purchase_id.analytic_account_ids:
                names = []
                for ad in self.purchase_id.analytic_account_ids:
                    if ad.is_suffix:
                        names.append(ad.name)
                if names:
                    update_values["analytic_category"] = "-" + "-".join(names)
            lots.write(update_values)

    def _action_done(self):
        self._set_channel_category()
        return super()._action_done()

    def button_validate(self):
        self._set_channel_category()
        return super().button_validate()
