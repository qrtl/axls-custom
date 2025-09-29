# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_via_plm = fields.Boolean(readonly=True)
    is_draft = fields.Boolean(
        help="Indicates if the product is in draft state. Selected when the product is "
        "first created from PLM import, and unselected when the product is confirmed "
        "(unarchived).",
    )

    def action_unarchive(self):
        res = super().action_unarchive()
        self.filtered(lambda p: p.is_draft).write({"is_draft": False})
        return res
