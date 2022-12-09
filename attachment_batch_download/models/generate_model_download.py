# Copyright 2022 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class GenerateModelDownload(models.Model):
    _name = "generate.model.download"

    name = fields.Char(required=True, states={"generated": [("readonly", True)]})
    model_id = fields.Many2one(
        "ir.model",
        "Model",
        help="Select model for which you want to generate server action.",
        states={"generated": [("readonly", True)]},
        ondelete="set null",
        index=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("generated", "Generated")],
        required=True,
        default="draft",
    )
    action_id = fields.Many2one(
        "ir.actions.server",
        string="Action",
        states={"generated": [("readonly", True)]},
    )

    def generate(self):
        """Generate server action for downloading attachments on model"""
        server_model = self.env["ir.actions.server"]
        for record in self:
            vals = {
                "name": _("Download"),
                "model_id": record.model_id.id,
                "state": "code",
                "code": """if records:
                action = records.action_download_attachment()""",
            }
            server_action = server_model.sudo().create(vals)
            server_action.create_action()
            record.write({"state": "generated", "action_id": server_action.id})
        return True

    def remove(self):
        for record in self:
            # Remove the shortcut to view server action
            server_action = record.action_id
            if server_action:
                server_action.unlink()
        self.write({"state": "draft"})
        return True
