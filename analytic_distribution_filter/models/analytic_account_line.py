# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models


class AnalyticAccountLine(models.Model):
    _name = "analytic.account.line"

    account_id = fields.Many2one("account.analytic.account", ondelete="cascade")
    plan_id = fields.Many2one("account.analytic.plan", required=True)
    account_ids = fields.Many2many(
        "account.analytic.account", string="Related Accounts", required=True
    )

    @api.onchange("plan_id")
    def onchange_plan_id(self):
        self.account_ids = False

    def _search_reciprocal(self, account_id, plan_id):
        return self.search(
            [
                ("account_id", "=", account_id),
                ("plan_id", "=", plan_id),
            ],
            limit=1,
        )

    def _update_reciprocal_relations(self, old_account_ids=None):
        for line in self:
            current_ids = set(line.account_ids.ids)
            old_ids = set(old_account_ids or [])
            added_ids = current_ids - old_ids
            removed_ids = old_ids - current_ids
            for account_id in added_ids:
                reciprocal = self._search_reciprocal(
                    account_id, line.account_id.plan_id.id
                )
                if reciprocal:
                    if line.account_id.id not in reciprocal.account_ids.ids:
                        reciprocal.account_ids = [Command.add(line.account_id.id)]
                else:
                    self.create(
                        {
                            "account_id": account_id,
                            "plan_id": line.account_id.plan_id.id,
                            "account_ids": [Command.set([line.account_id.id])],
                        }
                    )
            for account_id in removed_ids:
                reciprocal = self._search_reciprocal(
                    account_id, line.account_id.plan_id.id
                )
                if reciprocal and line.account_id.id in reciprocal.account_ids.ids:
                    reciprocal.account_ids = [Command.unlink(line.account_id.id)]
                    if not reciprocal.account_ids:
                        reciprocal.unlink()

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for record in res:
            record._update_reciprocal_relations()
        return res

    def write(self, vals):
        for record in self:
            old_ids = record.account_ids.ids
            super().write(vals)
            record._update_reciprocal_relations(old_account_ids=old_ids)
        return True

    def unlink(self):
        for record in self:
            for acc in record.account_ids:
                reciprocal = self._search_reciprocal(
                    acc.id, record.account_id.plan_id.id
                )
                if reciprocal and record.account_id.id in reciprocal.account_ids.ids:
                    reciprocal.account_ids = [Command.unlink(record.account_id.id)]
                    if not reciprocal.account_ids:
                        reciprocal.unlink()
        return super().unlink()
