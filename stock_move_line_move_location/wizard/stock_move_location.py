# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from itertools import groupby

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.fields import first


class StockMoveLocationWizard(models.TransientModel):
    _inherit = "wiz.stock.move.location"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get("active_model", False) != "stock.move.line":
            return res
        # Load data from move lines
        move_lines = self.env["stock.move.line"].browse(
            self.env.context.get("active_ids", False)
        )
        if len(move_lines.location_dest_id) > 1:
            raise UserError(
                _("There is more than one location in selected move lines.")
            )
        res["stock_move_location_line_ids"] = self.with_context(
            move_line_move_location=True
        )._prepare_wizard_move_lines(move_lines)
        res["origin_location_id"] = first(move_lines).location_dest_id.id
        return res

    @api.model
    def _prepare_wizard_move_lines(self, move_lines):
        res = []
        if not self.env.context.get("move_line_move_location", False):
            return super()._prepare_wizard_move_lines(move_lines)
        # if need move only available qty per product on location
        for _product, ml in groupby(
            sorted(move_lines, key=lambda r: (r.product_id, r.lot_id)),
            lambda r: (r.product_id, r.lot_id),
        ):
            quant = self.env["stock.quant"]
            ml = list(ml)[0]
            qty = quant._get_available_quantity(
                ml.product_id,
                ml.location_dest_id,
                ml.lot_id,
                strict=True,
            )
            if qty:
                vals = {
                    "product_id": ml.product_id.id,
                    "move_quantity": qty,
                    "max_quantity": qty,
                    "origin_location_id": ml.location_dest_id.id,
                    "lot_id": ml.lot_id.id,
                    "product_uom_id": ml.product_id.uom_id.id,
                    "custom": False,
                }
                res.append((0, 0, vals))
        return res
