# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models , fields


class StockStorage(models.Model):
    _name = "stock.storage"
    _description = "Stock Storage"

    company_id = fields.Many2one("res.company")
    product_id = fields.Many2one("product.product")
    location_id = fields.Many2one("stock.location")
    shelf = fields.Char()
    bucket = fields.Char()
    position = fields.Char()
    memo = fields.Char()
    ref = fields.Char("Internal Reference")
    generated_id = fields.Char(compute="compute_generated_id")

    @api.depends('shelf', 'bucket', 'position')
    def compute_generated_id(self):
        for record in self:
            record.generated_id = '-'.join([record.shelf or '', record.bucket or '', record.position or ''])

