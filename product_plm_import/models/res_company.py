# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    plm_path = fields.Char(
        "PLM Path",
        placeholder="e.g. /mnt/plmprod/CSV",
        help="Path to PLM CSV files. It can end with a slash (/) or without - both are "
        "acceptable.",
    )
    plm_last_import_date = fields.Datetime(
        "PLM Last Import Date",
        help="This date is updated every time PLM files for import are searched in PLM "
        "Path, and is used as a threshold for the next search.",
    )
    plm_notif_body = fields.Html("PLM Notification Body", translate=True)
    plm_notif_group_ids = fields.Many2many("res.groups", string="PLM Notified Groups")
