# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    account_manager_ids = fields.Many2many("res.users")

    @api.model_create_multi
    def create(self, vals_list):
        projects = super(ProjectProject, self).create(vals_list)
        for project in projects:
            if project.account_manager_ids:
                partner_ids = project.account_manager_ids.mapped("partner_id").ids
                project.message_subscribe(partner_ids=partner_ids)
        return projects

    def write(self, vals):
        res = super(ProjectProject, self).write(vals)
        if "account_manager_ids" in vals:
            for project in self:
                if project.account_manager_ids:
                    partner_ids = project.account_manager_ids.mapped("partner_id").ids
                    project.message_subscribe(partner_ids=partner_ids)
        return res
