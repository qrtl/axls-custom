from odoo import fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    stock_picking_accounting_date = fields.Date("Accounting Date", store=True)
