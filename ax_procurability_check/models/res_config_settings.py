# Copyright 2022 Axelspace
# License Other proprietary.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    octopart_client_id = fields.Char(
        string="Client ID for Octopart API",
        related="company_id.octopart_client_id",
        readonly=False,
        help="Set client id which is issued on nexar api settings page",
    )

    octopart_client_secret = fields.Char(
        string="Client secret for Octopart API",
        related="company_id.octopart_client_secret",
        readonly=False,
        help="Set client secret which is issued on nexar api settings page",
    )
    octopart_update_once = fields.Integer(
        string="Number of records to be updated at once",
        related="company_id.octopart_update_once",
        readonly=False,
        help="Number of records to be updated at once",
    )
