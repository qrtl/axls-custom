# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    no_owner = fields.Boolean()

    def _check_owner(self):
        """The check is skipped during test runs, so that tests of other modules
        that confirm purchase orders are not affected. Tests of this module opt in
        with the test_purchase_order_no_owner context key.
        """
        if config["test_enable"] and not self.env.context.get(
            "test_purchase_order_no_owner"
        ):
            return
        for record in self:
            if not record.no_owner and not record.owner_id:
                raise UserError(
                    _(
                        "Please select the owner. if you don't want to select any owner for"
                        " this order, you can set No Owner field as True."
                    )
                )

    def button_confirm(self):
        self._check_owner()
        return super(PurchaseOrder, self).button_confirm()

    @api.onchange("no_owner")
    def onchange_no_owner(self):
        if self.no_owner and self.owner_id:
            self.owner_id = False
