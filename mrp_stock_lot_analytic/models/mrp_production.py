# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _prepare_stock_lot_values(self):
        self.ensure_one()
        vals = super()._prepare_stock_lot_values()
        if self.analytic_distribution:
            vals["analytic_distribution"] = self.analytic_distribution
        return vals
