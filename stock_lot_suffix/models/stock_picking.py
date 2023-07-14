# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _set_channel_category(self):
        for picking in self:
            lots = self.move_line_ids.lot_id
            if lots:
                update_values = {}
                if picking.purchase_id.channel_category:
                    update_values[
                        "channel_category"
                    ] = picking.purchase_id.channel_category
                if picking.purchase_id.analytic_account_ids:
                    names = []
                    for ad in picking.purchase_id.analytic_account_ids:
                        if ad.analytic_category:
                            names.append(ad.analytic_category)
                    if names:
                        update_values["analytic_category"] = "-".join(names)
                lots.write(update_values)

    def _action_done(self):
        self._set_channel_category()
        return super()._action_done()

    def button_validate(self):
        self._set_channel_category()
        return super().button_validate()
