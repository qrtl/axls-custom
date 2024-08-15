# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BudgetCode(models.Model):
    _name = "budget.code"

    code = fields.Char(required=True)
    name = fields.Char(string="Description", required=True, translate=True)
    parent_id = fields.Many2one("budget.code", string="Parent Code")
    full_code = fields.Char(compute="_compute_full_code")
    full_description = fields.Char(compute="_compute_full_description")

    @api.depends("code", "parent_id.full_code")
    def _compute_full_code(self):
        for code in self:
            if code.parent_id:
                code.full_code = "%s%s" % (code.parent_id.full_code, code.code)
            else:
                code.full_code = code.code

    @api.depends("name", "parent_id.full_description")
    def _compute_full_description(self):
        for code in self:
            if code.parent_id:
                code.full_description = "%s - %s" % (
                    code.parent_id.full_description,
                    code.name,
                )
            else:
                code.full_description = code.name

    def name_get(self):
        name_list = []
        for rec in self:
            name = "[" + rec.full_code + "] " + rec.full_description
            name_list.append((rec.id, name))
        return name_list
