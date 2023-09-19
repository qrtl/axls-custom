# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class PlmDataImportLog(models.Model):
    _name = "plm.import.log"
    _inherit = "data.import.log"
    _description = "PLM Data Import Log"

    plm_product_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("failed", "Failed"),
            ("done", "Done"),
            ("na", "N/A"),
        ],
        compute="_compute_plm_product_state",
        store=True,
        tracking=True,
    )
    plm_product_ids = fields.One2many(
        "product.plm", "log_id", string="Imported PLM Products"
    )
    notification_sent = fields.Boolean(copy=False)

    @api.depends("plm_product_ids.state", "plm_product_ids.solved")
    def _compute_plm_product_state(self):
        for rec in self:
            # processed_init = rec.processed
            if not rec.plm_product_ids:
                rec.plm_product_state = "na"
                continue
            if all(
                plm_prod.state == "done" or plm_prod.solved
                for plm_prod in rec.plm_product_ids
            ):
                rec.plm_product_state = "done"
            elif any(
                plm_prod.state == "failed" and not plm_prod.solved
                for plm_prod in rec.plm_product_ids
            ):
                rec.plm_product_state = "failed"
            else:
                rec.plm_product_state = "draft"

    @api.model
    def _get_state_description(self, state_field, state_val, rec=None):
        if not rec:
            rec = self
        # Use list comprehension to filter out the description
        return next(
            (
                desc
                for value, desc in rec._fields[state_field].selection
                if value == state_val
            ),
            None,
        )

    @api.model
    def _get_plm_notification_domain(self):
        return [("notification_sent", "=", False)]

    @api.model
    def _send_plm_import_notification(self):
        domain = self._get_plm_notification_domain()
        log_recs = self.search(domain)
        for rec in log_recs:
            company = rec.company_id
            notified_groups = company.plm_notif_group_ids
            notified_partners = notified_groups.users.partner_id
            if not notified_partners:
                return
            rec.message_subscribe(partner_ids=notified_partners.ids)
            state_desc = rec._get_state_description(
                "plm_product_state", rec.plm_product_state
            )
            subject = state_desc + _(
                " [Odoo] Product IF Notification: %s", rec.file_name
            )
            body = _(
                f"<p><strong>Import File</strong>: {rec.file_name}</p>"
                f"<p><strong>Status</strong>: {state_desc}</p>",
            )
            if company.plm_notif_body:
                body += f"<p>{company.plm_notif_body}</p>"
            style = "border: 1px solid black; padding: 5px;"
            table = f"""
            <table style="border-collapse: collapse;">
                <tr>
                    <th style="{style}">PLM P/N</th>
                    <th style="{style}">State</th>
                    <th style="{style}">Message</th>
                </tr>
            """
            for plm_prod in rec.plm_product_ids:
                row_state_desc = rec._get_state_description(
                    "state", plm_prod.state, plm_prod
                )
                row = f"""
                <tr>
                    <td style="{style}">{plm_prod.part_number}</td>
                    <td style="{style}">{row_state_desc}</td>
                    <td style="{style}">{plm_prod.error_message or ""}</td>
                </tr>
                """
                table += row
            table += "</table>"
            body += table
            rec.message_post(
                subject=subject, body=body, subtype_xmlid="mail.mt_comment"
            )
            rec.write({"notification_sent": True})
