# Copyright 2020-2023 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import csv
import io
import logging
from base64 import b64decode
from collections import OrderedDict
from datetime import datetime
from html import escape, unescape

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DataImport(models.TransientModel):
    _name = "data.import"
    _description = "Data Import"

    import_file = fields.Binary(string="File")
    file_name = fields.Char()
    # error_handling = fields.Selection(
    #     selection=[("stop", "Stop"), ("ignore", "Ignore")],
    #     help="If you select 'Stop', no record should be imported when there is an "
    #     "error in the import file (error log will be generated)."
    #     "If you select 'Ignore', the import process will continue for all records "
    #     "except for the ones with an error.",
    #     default="stop",
    # )
    import_log_id = fields.Many2one("data.import.log", string="Import Log")

    # def _create_attachment(self, file_name, file_data):
    #     return self.env["ir.attachment"].create(
    #         {
    #             "name": file_name,
    #             "datas": file_data,
    #         }
    #     )

    def _create_import_log(self, res_model_name, log_model_name=None):
        if not log_model_name:
            log_model_name = "data.import.log"
        res_model = self.env["ir.model"].search([("model", "=", res_model_name)])
        attachment = self.env["ir.attachment"]
        if self.import_file:
            attachment = self.env["ir.attachment"].create({"name": self.file_name, "datas": self.import_file})
        import_log = self.env[log_model_name].create(
            {
                "input_file": attachment.id,
                "import_user_id": self.env.user.id,
                "import_date": datetime.now(),
                "state": "failed",
                "model_id": res_model.id,
            }
        )
        return import_log

    def _get_field_defs(self, FIELD_KEYS, FIELD_VALS):
        ordered_index = OrderedDict(sorted(FIELD_KEYS.items()))
        field_defs = []
        for field in FIELD_VALS:
            field_def = {}
            for k, v in ordered_index.items():
                field_def[v] = field[k]
            field_defs.append(field_def)
        return field_defs

    @api.model
    def _csv_file_read(self):
        # This method is expected to be extended in the inherited class.
        return b""

    def _load_import_file(self, field_defs, encodings=None):
        """We assume that there is a header line in the imported CSV."""
        if encodings is None:
            encodings = ["utf-8"]
        csv_data = b64decode(self.import_log_id.input_file.datas)
        # csv_data = b64decode(self.import_file)
        # if self.import_file:
        #     csv_data = b64decode(self.import_file)
        # else:
        #     csv_data = self._csv_file_read()
        #     # csv_data = self._get_csv_data()
        sheet_fields = []
        for encoding in encodings:
            try:
                csv_data = csv_data.decode(encoding)
                csv_iterator = csv.reader(io.StringIO(csv_data), delimiter=",")
                sheet_fields = next(csv_iterator)
                break
            except Exception:
                _logger.exception("Error while capturing sheet fields.")
        if not sheet_fields:
            raise UserError(_("Invalid file!"))
        missing_columns = list(
            {field_def["label"] for field_def in field_defs} - set(sheet_fields)
        )
        if missing_columns:
            raise UserError(
                _("Following columns are missing: \n%s") % "\n".join(missing_columns)
            )
        return sheet_fields, csv_iterator

    def _check_value_type(self, field_type, value, date_formats):
        # numeric fields
        if field_type == "float":
            try:
                float(value)
                return False
            except Exception:
                return field_type
        # date fields
        elif field_type == "date":
            date = False
            for date_format in date_formats:
                try:
                    date = datetime.strptime(value, date_format)
                    break
                except Exception:
                    _logger.exception("Error while validating the date.")
            return field_type if not date else False

    def _unescape_field_vals(self, row_dict, field_list):
        """Revert escaping of HTML special characters (e.g. '&gt;') for some fields."""
        for key, val in row_dict.items():
            if val and key in field_list:
                row_dict[key] = unescape(val)
        return row_dict

    def _check_field_vals(self, field_defs, row, sheet_fields, date_formats=None):
        if date_formats is None:
            date_formats = ["%Y-%m-%d", "%Y/%m/%d"]
        error_list = []
        row_dict = {}
        for field_def in field_defs:
            field = field_def["field"]
            label = field_def["label"]
            field_type = field_def["field_type"]
            required = field_def["required"]
            value = escape(row[sheet_fields.index(label)])
            if required and not value:
                error_list.append(_("%(label)s is missing.", label=label))
            else:
                # row_dict[field] = value
                errored_type = self._check_value_type(field_type, value, date_formats)
                if errored_type:
                    message = _(
                        "Unexpected value for %(label)s (%(errored_type)s)",
                        label=label,
                        errored_type=errored_type,
                    )
                    error_list.append(message)
            row_dict[field] = value
        return row_dict, error_list

    def _action_open_import_log(self, import_log, view_id=None, log_model_name=None):
        if not log_model_name:
            log_model_name = "data.import.log"
        if not view_id:
            view_id = self.env.ref("base_data_import.data_import_log_form").id
        return {
            "type": "ir.actions.act_window",
            "name": _("Import Result"),
            "res_model": log_model_name,
            "view_type": "form",
            "view_mode": "form",
            "res_id": import_log.id,
            "view_id": view_id,
            "target": "current",
        }
