# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    acceptance_tester_id = fields.Many2one(
        "res.partner", domain=[("is_acceptance_tester", "=", True)]
    )
