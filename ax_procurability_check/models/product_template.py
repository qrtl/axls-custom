# Copyright 2022 Axelspace
# License Other proprietary.

from odoo import api, fields, models


class ProductTemplate(models.Model):

    _inherit = "product.template"

    procure_info_id = fields.Many2one(
        "ax_prod_procurability",
        string="Procure Info",
        ondelete="restrict",
        readonly=True,
    )
    lifecycle = fields.Char(string="Lifecycle(Auto)", compute="_compute_lifecycle")
    lifecycle_m = fields.Char(
        string="LifeCycle(Manual)", compute="_compute_lifecycle_m"
    )
    octopart_url = fields.Char(
        "Stock Info URL",
        related="procure_info_id.octopart_url",
        readonly=True,
    )

    @api.depends("procure_info_id")
    def _compute_lifecycle(self):
        self.lifecycle = self.procure_info_id.lifecycle

    @api.depends("procure_info_id")
    def _compute_lifecycle_m(self):
        self.lifecycle_m = self.procure_info_id.lifecycle_m
