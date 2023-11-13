# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class CrmLead(models.Model):
    _inherit = ["crm.lead", "base.exception"]
    _name = "crm.lead"
    _order = "main_exception_id asc, name desc"

    @api.model
    def _reverse_field(self):
        return "crm_lead_ids"

    def _rule_domain(self):
        base_rule_domain = super()._rule_domain()
        rule_domain = expression.AND([base_rule_domain, [("id", "in", self.stage_id.exception_ids.ids)]])
        return rule_domain

    @api.constrains("ignore_exception", "stage_id")
    def _check_quantity_positive(self):
        for record in self:
            self._check_exception()
