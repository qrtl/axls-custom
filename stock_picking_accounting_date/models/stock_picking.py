# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    accounting_date = fields.Date(
        states={"done": [("readonly", True)], "cancel": [("readonly", True)]},
        help="Accounting date for journal entry of SVL.",
    )
