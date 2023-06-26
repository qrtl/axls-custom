# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    accounting_date = fields.Date(
        related="picking_id.accounting_date",
    )
    scheduled_date = fields.Date(
        related="picking_id.scheduled_date",
    )
    acceptance_date = fields.Date(
        compute="_compute_acceptance_date",
        store=True,
    )

    @api.depends("accounting_date", "scheduled_date")
    def _compute_acceptance_date(self):
        for line in self:
            if line.accounting_date:
                line.acceptance_date = line.accounting_date
            else:
                line.acceptance_date = line.scheduled_date
