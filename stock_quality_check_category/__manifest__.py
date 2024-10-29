# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Quality Check Category",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Stock",
    "license": "AGPL-3",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/quality_check_category_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
