# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "api.call.mixin"]

    jobcan_wf_number = fields.Char(string="Jobcan Workflow Number")
    warning_message = fields.Text(readonly=True)
    show_jobcan_wf_number = fields.Boolean(compute="_compute_jobcan_wf_number")

    def _compute_jobcan_wf_number(self):
        for pick in self:
            pick.show_jobcan_wf_number = False
            if pick.location_id.usage in [
                "internal",
                "transit",
            ] and pick.location_dest_id.usage not in ["internal", "transit"]:
                pick.show_jobcan_wf_number = True

    def button_validate(self):
        wf_transfers = self.filtered(lambda x: x.show_jobcan_wf_number)
        validated_pickings = self.env["stock.picking"]
        for picking in wf_transfers:
            try:
                params = {"id": picking.jobcan_wf_number}
                response = picking.make_api_call(
                    "jobcan", endpoint="v2/requests", params=params
                )
                response.raise_for_status()
                results = response.json().get("results", [])
                if results and results[0].get("status") == "completed":
                    validated_pickings |= picking
                    picking.warning_message = False
                else:
                    picking.warning_message = "Jobcan workflow is not completed."
            except Exception as e:
                picking.warning_message = "API call failed: {}".format(str(e))
                _logger.error(
                    "API call failed for picking %s with error: %s", picking.id, str(e)
                )
        transfers = self - wf_transfers
        if validated_pickings:
            transfers |= validated_pickings
        return super(StockPicking, transfers).button_validate()
