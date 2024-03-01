# Copyright 2024 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    force_oauth_domains = fields.Char(help="Fill in the domains, separated by commas.")
