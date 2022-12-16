# Copyright 2022 Axelspace
# License Other proprietary.

from odoo import fields, models


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    x_purchase_subsidy = fields.Char(string="Subsidy")
