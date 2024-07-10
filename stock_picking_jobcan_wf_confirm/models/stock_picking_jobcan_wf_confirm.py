import logging

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPickingJobcanWfConfirm(models.Model):
    _name = "stock.picking.jobcan.wf.confirm"
    _description = "Stock Picking Jobcan Workflow Confirm"
    _inherit = ["api.call.mixin"]

    @api.model
    def _scheduled_update(self):
        _logger.info("Scheduled stock picking JobCan WF confirmation...")
        pickings = self._get_assigned_pickings_with_jobcan_wf()
        confirm_pickings = self._get_confirmed_pickings(pickings)

        self._validate_confirmed_pickings(confirm_pickings)

    def _get_assigned_pickings_with_jobcan_wf(self):
        return self.env["stock.picking"].search(
            [("state", "=", "assigned"), ("jobcan_wf_number", "!=", False)]
        )

    def _get_confirmed_pickings(self, pickings):
        confirm_pickings = []
        for picking in pickings:
            try:
                results = self._make_api_call_for_picking(picking)
                if results and results[0].get("status") == "completed":
                    confirm_pickings.append(picking)
            except UserError as e:
                self.notify_user(picking, str(e))
        return confirm_pickings

    def _make_api_call_for_picking(self, picking):
        try:
            params = {"id": picking.jobcan_wf_number}
            response = picking.make_api_call(
                "jobcan_wf", endpoint="v2/requests", params=params
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            _logger.error(
                "API call failed for picking %s with error: %s", picking.id, str(e)
            )
            raise UserError(_("API call failed: {}".format(str(e)))) from e

    def _validate_confirmed_pickings(self, confirm_pickings):
        for picking in confirm_pickings:
            try:
                picking.button_validate()
            except UserError as e:
                self.notify_user(picking, str(e))

    def get_api_key(self, config):
        api_key = self.env["base.api.connection"].get_api_key(config)
        if config.code == "jobcan_wf":
            api_key = "Token " + api_key
        return api_key

    def notify_user(self, picking, message):
        if picking.user_id:
            channel = self._get_or_create_channel(picking)
            picking_url = f"/web#id={picking.id}&model=stock.picking&view_type=form"
            message_body = _(
                'JobCan WF ID %s has been approved but picking <a href="%s">%s</a> failed to confirm.<br/>Details:<br/>%s'
            ) % (
                picking.jobcan_wf_number,
                picking_url,
                picking.name,
                message,
            )
            subject = _("Picking Confirmation Failed: %s") % (picking.name,)
            channel.message_post(
                body=message_body,
                subject=subject,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
                partner_ids=[picking.user_id.partner_id.id],
            )

    def _get_or_create_channel(self, picking):
        channel_name = f"picking_{picking.id}_notifications"
        channel = self.env["mail.channel"].search(
            [("name", "=", channel_name)], limit=1
        )
        if not channel:
            channel = self.env["mail.channel"].create(
                {
                    "name": channel_name,
                    "channel_type": "chat",
                    "channel_partner_ids": [(4, picking.user_id.partner_id.id)],
                }
            )
        return channel
