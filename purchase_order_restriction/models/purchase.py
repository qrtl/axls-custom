# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    restrict_purchase_order = fields.Boolean(
        "Restrict Order",
        help="If set as True, purchase order can only be accessed by Purchase Manager",
    )
