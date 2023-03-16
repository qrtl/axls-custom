# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Stock Storage",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Stock",
    "license": "LGPL-3",
    "depends": ["product","stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_move_line_views.xml",
        "views/stock_move_views.xml",
        "views/product_template_views.xml",
        "views/stock_storage_views.xml",
    ],
    "installable": True,
}
