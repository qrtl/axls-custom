# Copyright 2023 Quartile Limited

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    plm_path = fields.Char()
    plm_last_import_date = fields.Datetime()
    plm_notif_body = fields.Html("PLM Notification Body", translate=True)
    plm_notif_group_ids = fields.Many2many("res.groups", string="PLM Notified Groups")
