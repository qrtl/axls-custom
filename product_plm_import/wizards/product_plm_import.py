# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os
from base64 import b64encode
from datetime import datetime, timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


FIELD_KEYS = {0: "field", 1: "label", 2: "field_type", 3: "required"}

# Prepare values corresponding with the keys
FIELD_VALS = [
    ["part_number", "Part Number", "char", True],
    ["name", "Name", "char", True],
    ["esc_code", "ESC ID", "char", False],
    ["procure_flag", "Procure flag", "char", True],
    ["item_type", "Item Type", "char", True],
    ["category", "Category", "char", True],
    ["uom", "Unit of Material", "char", True],
    ["description", "Description", "char", True],
    ["spec", "Spec", "char", False],
    ["drawing", "Drawing No", "char", False],
    ["generic_name", "Generic Name", "char", False],
]

FIELD_TO_UNESCAPE = [
    "name",
    "category",
    "description",
    "spec",
    "drawing",
    "generic_name",
]


class ProductPlmImport(models.TransientModel):
    _name = "product.plm.import"
    _inherit = "data.import"
    _description = "Product PLM Import"

    import_log_id = fields.Many2one("plm.import.log")

    @api.model
    def _get_product_domain(self, part_number):
        return [
            "&",
            "|",
            ("default_code", "=", part_number),
            ("alt_code", "=", part_number),
            "&",
            "|",
            ("company_id", "=", self.env.company.id),
            ("company_id", "=", False),
            "|",
            ("active", "=", True),
            ("active", "=", False),
        ]

    @api.model
    def _update_vals_list(self, row_dict, error_list, vals_list):
        company = self.env.company
        part_number = row_dict.get("part_number")
        product_domain = self._get_product_domain(part_number)
        product = self.env["product.product"].search(product_domain)
        if product:
            error_list.append(_("There is already a product for %s.", part_number))
        # We update vals_list regardless of whether there is an error or not
        row_dict["company_id"] = company.id
        row_dict["log_id"] = self.import_log_id.id
        # TODO: Find a better way to handle unescaping.
        row_dict = self._unescape_field_vals(row_dict, FIELD_TO_UNESCAPE)
        vals_list.append(row_dict)

    def import_product_plm(self, attachment=None):
        # In case this method is called via a cron method.
        if not self:
            self = self.create({})
        self.ensure_one()
        # To send notification emails in English
        self = self.with_context(lang="en_US")
        self.import_log_id = self._create_import_log("product.plm", "plm.import.log")
        if not self.import_log_id.input_file and attachment:
            self.import_log_id.input_file = attachment
        field_defs = self._get_field_defs(FIELD_KEYS, FIELD_VALS)
        sheet_fields, csv_iterator = self._load_import_file(
            field_defs, ["cp932", "utf-8-sig", "utf-8"]
        )
        vals_list = []
        # csv_iterator.line_num gets incremented by more than 1 when there is a text
        # field with a line break. Therefore, we need to use our own counter.
        # The counter will effectively start with 2 which is the first row after the
        # header.
        row_no = 1
        for row in csv_iterator:
            row_no += 1
            row_dict, error_list = self._check_field_vals(field_defs, row, sheet_fields)
            row_dict["row_no"] = row_no
            # Here is the module specific logic
            if row_dict:
                self._update_vals_list(row_dict, error_list, vals_list)
            if error_list:
                # We are not using date.import.error in this module.
                row_dict["error_message"] = "\n".join(error_list)
                row_dict["state"] = "failed"
        plm_recs = self.env["product.plm"].create(vals_list)
        for plm_rec in plm_recs:
            plm_rec.mapping_id = plm_rec._get_plm_product_mapping()
            if not plm_rec.mapping_id:
                plm_rec.write(
                    {
                        "error_message": _("No PLM-product mapping record found."),
                        "state": "failed",
                    }
                )
        self.env.ref(
            "product_plm_import.ir_cron_create_products_for_plm_import"
        )._trigger()
        self.env.ref(
            "product_plm_import.ir_cron_send_plm_import_notification"
        )._trigger(fields.Datetime.now() + timedelta(minutes=1))
        if attachment:
            return True
        view_id = self.env.ref("product_plm_import.view_product_plm_import_log_form").id
        return self._action_open_import_log(
            self.import_log_id, view_id, "plm.import.log"
        )

    def _get_new_plm_files(self, plm_path):
        company = self.env.company
        threshold_date = company.plm_last_import_date or (
            fields.Datetime.now() - timedelta(days=1)
        )
        company.plm_last_import_date = fields.Datetime.now()
        all_files = os.listdir(plm_path)
        # Filter the CSV files that are newer than the threshold date
        return [
            file
            for file in all_files
            if file.endswith(".csv")
            and datetime.fromtimestamp(os.path.getmtime(os.path.join(plm_path, file)))
            > threshold_date
        ]

    def _create_plm_attachments(self, new_files, plm_path):
        attachments = self.env["ir.attachment"]
        for file_name in new_files:
            plm_file_path = os.path.join(plm_path, file_name)
            try:
                with open(plm_file_path, "rb") as file:
                    file_content = file.read()
                    encoded_content = b64encode(file_content)
                    attachment = self.env["ir.attachment"].create(
                        {
                            "name": file_name,
                            "type": "binary",
                            "datas": encoded_content,
                            "mimetype": "text/csv",
                        }
                    )
                    attachments += attachment
            except Exception as e:
                _logger.error(
                    "ProductPlmImport._create_plm_attachments - failed to read and "
                    "encode the file: %s",
                    str(e),
                )
        return attachments

    @api.model
    def import_product_from_plm_path(self):
        plm_path = self.env.company.plm_path
        new_files = self._get_new_plm_files(plm_path)
        # Avoid importing files that are already imported (identify those by name)
        attachments = self.env["ir.attachment"].search([("name", "in", new_files)])
        for attachment in attachments:
            new_files.remove(attachment.name)
        new_attachments = self._create_plm_attachments(new_files, plm_path)
        for new_attachment in new_attachments:
            self.import_product_plm(new_attachment)
