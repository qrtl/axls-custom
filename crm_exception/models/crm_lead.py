# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class CrmLead(models.Model):
    _inherit = ["crm.lead", "base.exception"]
    _name = "crm.lead"
    _order = "main_exception_id asc, name desc"

    @api.model
    def _reverse_field(self):
        return "crm_lead_ids"

    def _fields_trigger_check_exception(self):
        return ["ignore_exception", "stage_id"]

    def crm_check_exception(self):
        self._check_exception()

    def _check_crm_lead_check_exception(self, vals):
        check_exceptions = any(
            field in vals for field in self._fields_trigger_check_exception()
        )
        if check_exceptions:
            self.crm_check_exception()

    def write(self, vals):
        result = super().write(vals)
        self._check_crm_lead_check_exception(vals)
        return result
