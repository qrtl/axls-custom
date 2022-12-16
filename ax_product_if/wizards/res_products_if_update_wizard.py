# Copyright 2022 Axelspace
# Other proprietary.

from odoo import fields, models


class ResProductsIfUpdateWizard(models.TransientModel):

    _name = "res.products.if.update.wizard"
    _description = "Products IF Update Wizard"

    date_from = fields.Date(
        string="Start Date", required=True, default=fields.Date.context_today
    )
    date_to = fields.Date(
        string="End Date", required=True, default=fields.Date.context_today
    )
    provider_ids = fields.Many2many(
        string="Providers",
        comodel_name="res.products.if.provider",
        column1="wizard_id",
        column2="provider_id",
    )

    def action_update(self):
        self.ensure_one()

        self.provider_ids._update(self.date_from, self.date_to)

        return {"type": "ir.actions.act_window_close"}
