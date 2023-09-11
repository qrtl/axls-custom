# Copyright 2020-2021 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class DataImportLog(models.Model):
    _name = "data.import.log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Data Import Log"
    _rec_name = "file_name"
    _order = "id DESC"

    import_date = fields.Datetime("Imported On")
    import_user_id = fields.Many2one("res.users", "Imported By")
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )
    error_ids = fields.One2many("data.import.error", "log_id", string="Log Lines")
    input_file = fields.Many2one("ir.attachment", string="File")
    file_path = fields.Binary(related="input_file.datas", string="Imported File")
    file_name = fields.Char(related="input_file.name")
    state = fields.Selection(
        [("failed", "Failed"), ("imported", "Imported"), ("done", "Done")],
        string="Status",
    )
    model_id = fields.Many2one("ir.model", string="Model")
    model_name = fields.Char(related="model_id.model", string="Model Name")
    # error_handling = fields.Selection(
    #     selection=[("stop", "Stop"), ("ignore", "Ignore")],
    #     help="If you select 'Stop', no record should be imported when there is an "
    #     "error in the import file (error log will be generated)."
    #     "If you select 'Ignore', the import process will continue for all records "
    #     "except for the ones with an error.",
    # )
