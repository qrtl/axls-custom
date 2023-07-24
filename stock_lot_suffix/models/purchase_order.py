# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "analytic.mixin"]

    channel_category = fields.Char()

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.channel_category = self.partner_id.channel_category
