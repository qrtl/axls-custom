# Copyright 2022 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO

import ast
import zipfile
from datetime import datetime

from odoo import http
from odoo.http import content_disposition, request


class Binary(http.Controller):
    @http.route("/web/binary/download_document", type="http", auth="public")
    def download_document(self, tab_id, **kw):
        new_tab = ast.literal_eval(tab_id)
        attachment_ids = request.env["ir.attachment"].search([("id", "in", new_tab)])
        file_dict = {}
        for attachment_id in attachment_ids:
            file_store = attachment_id.store_fname
            if file_store:
                file_name = attachment_id.name
                file_path = attachment_id._full_path(file_store)
                file_dict["%s:%s" % (file_store, file_name)] = dict(
                    path=file_path, name=file_name
                )
        zip_filename = datetime.now()
        zip_filename = "%s.zip" % zip_filename
        bitIO = BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
        for file_info in file_dict.values():
            zip_file.write(file_info["path"], file_info["name"])
        zip_file.close()
        return request.make_response(
            bitIO.getvalue(),
            headers=[
                ("Content-Type", "application/x-zip-compressed"),
                ("Content-Disposition", content_disposition(zip_filename)),
            ],
        )
