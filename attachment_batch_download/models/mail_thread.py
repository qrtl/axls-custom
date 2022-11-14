# Copyright 2022 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def action_download_attachment(self):
        tab_id = []
        attachment_ids = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self.env.context["active_model"]),
                ("res_id", "in", self.ids),
            ]
        )
        for attach in attachment_ids:
            tab_id.append(attach.id)
        url = "/web/binary/download_document?tab_id=%s" % tab_id
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }
