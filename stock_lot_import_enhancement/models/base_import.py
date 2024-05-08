# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class Import(models.TransientModel):
    _inherit = "base_import.import"

    @api.model
    def _convert_import_data(self, fields, options):
        data, import_fields = super(Import, self)._convert_import_data(fields, options)
        model = self.env["ir.model"].sudo().search([("model", "=", self.res_model)])
        lot_index_column = model.lot_index_column
        product_index_column = model.product_index_column
        if not lot_index_column or not product_index_column:
            return data, import_fields
        product_index = (
            import_fields.index(product_index_column)
            if product_index_column in import_fields
            else -1
        )
        lot_index = (
            import_fields.index(lot_index_column)
            if lot_index_column in import_fields
            else -1
        )
        if product_index != -1 and lot_index != -1:
            for row in data:
                # Ensure the row has enough fields and the fields are not empty
                if (
                    len(row) > max(product_index, lot_index)
                    and row[product_index]
                    and row[lot_index]
                ):
                    product_name = row[product_index]
                    lot_name = row[lot_index]
                    # Append the product name to the lot_id value using a unique delimiter
                    row[lot_index] = f"{product_name}|{lot_name}"
        return data, import_fields
