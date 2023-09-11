# Copyright 2020-2021 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class DataImportError(models.Model):
    _name = "data.import.error"
    _description = "Data Import Error"

    row_no = fields.Integer("Row Number")
    reference = fields.Char()
    error_message = fields.Text("Message")
    log_id = fields.Many2one("data.import.log", string="Log")
