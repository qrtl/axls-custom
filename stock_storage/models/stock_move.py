# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    generated_id = fields.Char(compute="compute_generated_id",store=True)

    @api.depends("location_id","product_id")
    def compute_generated_id(self):
        for rec in self:
            storage_id = self.env["stock.storage"].search([('location_id', '=', rec.location_dest_id.id), ('product_id', '=', rec.product_id.id)],limit=1)
            if storage_id: 
                self.generated_id = storage_id.generated_id
            else:
                self.generated_id = False
        
