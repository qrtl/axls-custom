# Copyright 2020-2022 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Base Data Import",
    "version": "16.0.1.0.0",
    "category": "Hidden/Tools",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "license": "LGPL-3",
    "depends": ["mail"],
    "data": [
        "security/data_import_security.xml",
        "security/ir.model.access.csv",
        "views/data_import_log_views.xml",
        "wizards/data_import_views.xml",
    ],
    "installable": True,
}
