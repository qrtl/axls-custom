# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    barcode_label_analytic_plan_id = fields.Many2one(
        "account.analytic.plan",
        related="company_id.barcode_label_analytic_plan_id",
        string="Analytic plan shown on stock labels",
        domain="[('company_id', 'in', [False, company_id])]",
        # account.analytic.plan is readable only by the analytic accounting
        # group, so without this the field raises an AccessError out of its own
        # name_get for anyone else - including a settings administrator on a
        # database where analytic accounting is switched off.
        groups="analytic.group_analytic_accounting",
        readonly=False,
    )
