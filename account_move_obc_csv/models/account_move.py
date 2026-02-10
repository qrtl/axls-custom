# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_exported = fields.Boolean("Exported", copy=False)

    def action_unset_exported(self):
        """Unset is_exported field for selected records"""
        count = len(self)
        self.write({"is_exported": False})

        message = _("%(count)s record(s) unmarked as exported.") % {"count": count}
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": message,
                "sticky": False,
            },
        }
