# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    allow_location_discrepancy = fields.Boolean(
        copy=False,
        help="If enabled, no error is raised for location discrepancy between picking "
        "and its move lines at the time of validation.",
    )

    def _check_location_consistency(self, pick_location, line_locations):
        self.ensure_one()
        if not set(line_locations).issubset(pick_location.child_internal_location_ids):
            raise ValidationError(
                f"Location inconsistency found in picking {self.name}: "
                "Locations on the picking do not match with its move lines."
            )

    def _action_done(self):
        for pick in self:
            if pick.allow_location_discrepancy:
                continue
            if pick.location_id.usage == "internal":
                self._check_location_consistency(
                    pick.location_id, pick.move_line_ids.location_id
                )
            if pick.location_dest_id.usage == "internal":
                self._check_location_consistency(
                    pick.location_dest_id, pick.move_line_ids.location_dest_id
                )
        return super()._action_done()
