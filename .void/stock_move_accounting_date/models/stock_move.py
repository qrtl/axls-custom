# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    accounting_date = fields.Date(
        compute="_compute_accounting_date",
        store=True,
    )

    @api.depends("date", "accounting_date")
    def _compute_accounting_date(self):
        for line in self:
            line.accounting_date = line.date
            if line.picking_id.accounting_date:
                line.accounting_date = line.picking_id.accounting_date
