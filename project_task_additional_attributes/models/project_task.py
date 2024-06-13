# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    view_id_list = fields.Char(
        string="View ID", help="List of numeric values separated by commas."
    )
    is_feasible = fields.Selection([("yes", "Yes"), ("no", "No")], string="Feasible?")

    @api.constrains("view_id_list")
    def _check_view_id_list(self):
        for record in self:
            if record.view_id_list:
                try:
                    # Attempt to convert each value to an integer, allowing spaces
                    [
                        int(val.strip())
                        for val in record.view_id_list.replace(" ", "").split(",")
                    ]
                except ValueError as err:
                    raise ValidationError(
                        _("Please enter only numeric values in the View ID field.")
                    ) from err
