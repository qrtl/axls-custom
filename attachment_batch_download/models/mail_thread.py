# Copyright 2022 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def action_download_attachment(self):
        attachment_ids = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self.env.context["active_model"]),
                ("res_id", "in", self.ids),
            ]
        )
        url = "/web/binary/download_document?attachment_ids=%s" % attachment_ids.ids
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }
