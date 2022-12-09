# Copyright 2022 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Attachment Batch Download",
    "category": "Attachment",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "license": "AGPL-3",
    "depends": ["mail", "base"],
    "data": [
        "security/ir.model.access.csv",
        "views/generate_model_download.xml",
    ],
    "installable": True,
}
