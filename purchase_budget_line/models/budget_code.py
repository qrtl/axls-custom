# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BudgetCode(models.Model):
    _name = "budget.code"
    _order = "complete_code"
    _rec_names_search = ["complete_code", "complete_name_en", "complete_name_ja"]

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    parent_id = fields.Many2one("budget.code")
    analytic_account_id = fields.Many2one("account.analytic.account")
    complete_code = fields.Char(
        compute="_compute_complete_code",
        recursive=True,
        store=True,
    )
    complete_name_en = fields.Char(
        compute="_compute_complete_name",
        recursive=True,
        store=True,
    )
    complete_name_ja = fields.Char(
        compute="_compute_complete_name",
        recursive=True,
        store=True,
    )
    child_ids = fields.One2many(
        string="Child Budget Codes",
        comodel_name="budget.code",
        inverse_name="parent_id",
        copy=True,
    )
    active = fields.Boolean(default=True)

    @api.depends("code", "parent_id.complete_code")
    def _compute_complete_code(self):
        for rec in self:
            if rec.parent_id:
                rec.complete_code = "%s%s" % (rec.parent_id.complete_code, rec.code)
            else:
                rec.complete_code = rec.code

    def _get_complete_name_field(self, lang=None):
        self.ensure_one()
        if not lang:
            lang = self.env.context.get("lang", "en_US")
        return "complete_name_en" if lang.startswith("en") else "complete_name_ja"

    @api.depends("name", "parent_id.complete_name_en", "parent_id.complete_name_ja")
    def _compute_complete_name(self):
        for lang in ["en_US", "ja_JP"]:
            for rec in self.with_context(lang=lang):
                # Record creation fails without this.
                if isinstance(rec.id, models.NewId):
                    continue
                complete_name_field = rec._get_complete_name_field()
                if rec.parent_id:
                    complete_name_value = "%s-%s" % (
                        getattr(rec.parent_id, complete_name_field),
                        rec.name,
                    )
                else:
                    complete_name_value = rec.name
                setattr(rec, complete_name_field, complete_name_value)

    def name_get(self):
        name_list = []
        for rec in self:
            complete_name_field = rec._get_complete_name_field()
            complete_name = getattr(rec, complete_name_field)
            name = "[" + rec.complete_code + "] " + complete_name
            name_list.append((rec.id, name))
        return name_list
