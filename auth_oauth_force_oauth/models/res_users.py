# Copyright 2024 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _is_allowed_password_login(self):
        force_domains = self.company_id.force_oauth_domains
        if not force_domains:
            return True
        # Check if the login ends with any of the force domains
        force_domains_list = [domain.strip() for domain in force_domains.split(",")]
        if not any(self.login.endswith(domain) for domain in force_domains_list):
            return True
        return False
