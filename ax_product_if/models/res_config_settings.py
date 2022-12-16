# Copyright 2022 Axelspace
# License Other proprietary.
# res.config.settings は一時的(transient)で、自分で保存しなければならない。
# res.company modelを使用すると保存ができる。
# 他にも幾つか保存の方法はある。
# 参考
# https://gist.github.com/ryanc-me/a0e35fb6741d73c39f9e3968eaa485ee
# 個々の設定を変更した場合は、再インストールしてOdooを立ち上げ直さないと有効にならないかも。

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_interface = fields.Boolean(
        string="Product interface (Axelspace)",
        related="company_id.product_interface",
        readonly=False,
        help="Enable product interface",
    )

    product_interface_location = fields.Char(
        string="Interface file Location",
        related="company_id.product_interface_location",
        readonly=False,
        default="/mnt/ifdata",
        help="File location of interface data for product",
    )
