# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    no_owner = fields.Boolean()

    @api.constrains("no_owner", "owner_id")
    def _check_owner_id(self):
        for record in self:
            if not record.no_owner and not record.owner_id:
                raise UserError(
                    _(
                        "Please select the owner. if you don't want to select any owner for"
                        " this order, you can set No Owner field as True."
                    )
                )

    @api.onchange("no_owner")
    def onchange_no_owner(self):
        if self.no_owner and self.owner_id:
            self.owner_id = False
