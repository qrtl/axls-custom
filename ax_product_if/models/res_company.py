# Copyright 2022 Axelspace
# License Other proprietary.

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    product_interface = fields.Boolean(
        string="Product interface (Axelspace)",
        dafault=False,
        help="Enable product interface",
    )

    product_interface_location = fields.Char(
        string="Interface file Location",
        default="/mnt/ifdata",
        help="File location of interface data for product",
    )
