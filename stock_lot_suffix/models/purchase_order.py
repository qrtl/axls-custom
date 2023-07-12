# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    channel_category = fields.Char()

    @api.onchange("partner_id")
    def _onchange_channel_category(self):
        channel = self.partner_id.channel_category
        if channel:
            self.channel_category = channel
