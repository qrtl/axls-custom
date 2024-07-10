# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    role_ids = fields.Many2many(
        string="Roles",
        comodel_name="res.partner.role",
    )

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        vals = super()._prepare_customer_values(partner_name, is_company, parent_id)
        if self.role_ids:
            vals["role_ids"] = self.role_ids
        return vals
