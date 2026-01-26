# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    show_consumable_accounting_date = fields.Boolean(
        compute="_compute_show_consumable_accounting_date"
    )

    def _compute_show_consumable_accounting_date(self):
        for pick in self:
            pick.show_consumable_accounting_date = False
            if pick.picking_type_code not in ("incoming", "outgoing"):
                continue
            moves = pick.move_ids
            # When all moves are consumables.
            if moves and not moves.with_company(pick.company_id).product_id.filtered(
                lambda x: x.detailed_type == "product"
            ):
                pick.show_consumable_accounting_date = True
