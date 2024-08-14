# Copyright 2024 Quartile
# Copyright 2024 Axelspace Corporation (https://axelspace.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "api.call.mixin"]

    skip_jobcan_wf = fields.Boolean("Skip Jobcan Workflow", copy=False)
    show_skip_jobcan_wf = fields.Boolean(compute="_compute_show_skip_jobcan_wf")
    jobcan_wf_number = fields.Char("Jobcan Workflow Number", copy=False)
    show_jobcan_wf_number = fields.Boolean(compute="_compute_show_jobcan_wf_number")

    def _is_outgoing(self):
        self.ensure_one()
        return self.location_id.usage in [
            "internal",
            "transit",
        ] and self.location_dest_id.usage not in ["internal", "transit"]

    def _receipt_return_picking(self):
        self.ensure_one()
        if self.move_ids and self.move_ids == self.move_ids.filtered(
            lambda x: x.picking_id._is_outgoing() and x.origin_returned_move_id
        ):
            return True
        return False

    def _compute_show_skip_jobcan_wf(self):
        for pick in self:
            pick.show_skip_jobcan_wf = False
            if (
                pick._is_outgoing()
                and not pick._receipt_return_picking()
                and not pick.move_line_ids.mapped("owner_id")
            ):
                pick.show_skip_jobcan_wf = True

    @api.depends("skip_jobcan_wf")
    def _compute_show_jobcan_wf_number(self):
        for pick in self:
            pick.show_jobcan_wf_number = False
            if pick.show_skip_jobcan_wf and not pick.skip_jobcan_wf:
                pick.show_jobcan_wf_number = True

    def get_api_key(self, config):
        api_key = super().get_api_key(config)
        if config.code == "jobcan_wf":
            api_key = "Token " + api_key
        return api_key

    def _check_jobcan_wf_status(self):
        self.ensure_one()
        results = []
        if not self.jobcan_wf_number:
            raise UserError(_("Jobcan Workflow Number missing: %s") % (self.name))
        try:
            params = {"id": self.jobcan_wf_number}
            response = self.make_api_call(
                "jobcan_wf", endpoint="v2/requests", params=params
            )
            response.raise_for_status()
            results = response.json().get("results", [])
        except Exception as e:
            _logger.error(
                "API call failed for picking %s with error: %s", self.id, str(e)
            )
            raise UserError(_("API call failed: {}".format(str(e)))) from e
        if not results:
            raise UserError(
                _(
                    "Specified Jobcan Workflow Number '%(jobcan_wf_number)s' does "
                    "not exist: %(pick_name)s",
                    jobcan_wf_number=self.jobcan_wf_number,
                    pick_name=self.name,
                )
            )
        if results[0].get("status") != "completed":
            raise UserError(
                _(
                    "Jobcan workflow '%(jobcan_wf_number)s' is not completed: "
                    "%(pick_name)s",
                    jobcan_wf_number=self.jobcan_wf_number,
                    pick_name=self.name,
                )
            )

    def notify_user(self, message):
        self.ensure_one()
        if self.user_id:
            self_url = f"/web#id={self.id}&model=stock.picking&view_type=form"
            message_body = _(
                "JobCan WF ID %(wf_id)s has been approved but picking "
                '<a href="%(url)s">%(name)s</a> failed to confirm.<br/>Details:<br/>%(message)s'
            ) % {
                "wf_id": self.jobcan_wf_number,
                "url": self_url,
                "name": self.name,
                "message": message,
            }
            subject = _("Picking Confirmation Failed: %(name)s") % {"name": self.name}
            self.message_post(
                body=message_body,
                subject=subject,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
                partner_ids=[self.user_id.partner_id.id],
            )

    def button_validate(self):
        wf_transfers = self.filtered(lambda x: x.show_jobcan_wf_number)
        for pick in wf_transfers:
            pick._check_jobcan_wf_status()
        return super().button_validate()

    def _get_assigned_pickings_with_jobcan_wf(self):
        return self.search(
            [("state", "=", "assigned"), ("jobcan_wf_number", "!=", False)]
        )

    def _validate_pickings(self):
        for pick in self.with_context(skip_immediate=True):
            try:
                pick.move_ids._set_quantities_to_reservation()
                pick.button_validate()
            except Exception as e:
                pick.notify_user(str(e))

    @api.model
    def _run_stock_picking_jobcan_wf_confirmation(self):
        _logger.info("Scheduled stock picking JobCan WF confirmation...")
        pickings = self._get_assigned_pickings_with_jobcan_wf()
        pickings._validate_pickings()
