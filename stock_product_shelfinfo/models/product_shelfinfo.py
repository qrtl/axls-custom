# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductShelfinfo(models.Model):
    _name = "product.shelfinfo"
    _description = "Product Shelfinfo"
    _order = "sequence"

    name = fields.Char("Generated ID", compute="_compute_name")
    product_id = fields.Many2one(
        "product.product",
        required=True,
        domain="[('detailed_type', '!=', 'service')]",
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        related="product_id.product_tmpl_id",
        store=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        required=True,
        domain="[('usage', '=', 'internal')]",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    area1 = fields.Char(required=True)
    area2 = fields.Char()
    position = fields.Char()
    memo = fields.Char()
    ref = fields.Char("Internal Reference")
    sequence = fields.Integer(default=1)

    @api.constrains("product_id", "location_id", "company_id")
    def _check_product_location_unique(self):
        for record in self:
            existing_rec = self.search(
                [
                    ("product_id", "=", record.product_id.id),
                    ("location_id", "=", record.location_id.id),
                    ("company_id", "=", record.company_id.id),
                    ("id", "!=", self.id),
                ]
            )
            if existing_rec:
                raise ValidationError(
                    _(
                        "Another record already exists for the given combination of "
                        "product, location and company."
                    )
                )

    @api.depends("area1", "area2", "position")
    def _compute_name(self):
        for record in self:
            record.name = record.area1
            record.name = ""
            if record.area1:
                record.name += record.area1
            if record.area2:
                record.name += "-" + record.area2
            if record.position:
                record.name += "-" + record.position
