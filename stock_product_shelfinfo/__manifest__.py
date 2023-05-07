# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Product Shelf Information",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Warehouse",
    "license": "AGPL-3",
    "depends": ["stock"],
    "data": [
        "data/menuitem_data.xml",
        "security/ir.model.access.csv",
        "security/product_shelfinfo_security.xml",
        "reports/report_stockpicking_operations.xml",
        "views/product_shelf_area1_views.xml",
        "views/product_shelf_area2_views.xml",
        "views/product_shelf_position_views.xml",
        "views/product_shelfinfo_views.xml",
        "views/product_template_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
