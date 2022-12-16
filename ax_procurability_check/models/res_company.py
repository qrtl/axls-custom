# Copyright 2022 Axelspace
# License Other proprietary.

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    octopart_client_id = fields.Char(
        string="Client ID for Octopart API",
        help="Set client ID",
    )
    # TODO: DB 上に平文で保存されるの問題かも。どこかにそういう記事あったような。
    octopart_client_secret = fields.Char(
        string="Client secret for Octopart API",
        help="Set client secret",
    )
    octopart_update_once = fields.Integer(
        string="Update Once",
        help="Number of records to be updated at once",
    )
