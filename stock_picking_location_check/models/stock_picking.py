# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    allow_location_discrepancy = fields.Boolean(
        help="If enable, the location discrepancies will be allowed between picking "
        "and stock move lines."
    )

    @api.constrains("state")
    def _check_location_consistency(self):
        """Check consistency of locations between picking and its stock move lines."""
        for picking in self:
            if picking.allow_location_discrepancy:
                continue
            # Determine if the picking is an immediate transfer
            is_immediate_transfer = picking._check_immediate()
            for move_line in picking.move_line_ids:
                # If not an immediate transfer and qty_done is 0, skip this move line
                if not is_immediate_transfer and move_line.qty_done <= 0:
                    continue
                # Perform the location consistency check
                if (
                    picking.location_id != move_line.location_id
                    or picking.location_dest_id != move_line.location_dest_id
                ):
                    raise ValidationError(
                        f"Location inconsistency found in picking {picking.name}: "
                        "Locations on the picking do not match with its move lines."
                    )
        return True
