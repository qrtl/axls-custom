# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QualityCheckCategory(models.Model):
    _name = "quality.check.category"
    _description = "Quality Check Category"
    _order = "code"
    _rec_names_search = ["code", "description"]

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)

    def name_get(self):
        res = super().name_get()
        name_mapping = dict(res)
        for rec in self:
            if rec.code:
                name_mapping[rec.id] = "[" + rec.code + "] " + name_mapping[rec.id]
        return list(name_mapping.items())
