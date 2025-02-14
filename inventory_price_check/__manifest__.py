# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Inventory Price Check",
    "version": "16.0.1.0.0",
    "category": "Stock",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "depends": ["purchase_stock"],
    "license": "AGPL-3",
    "data": [
        "security/inventory_price_check_security.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "views/res_config_setting_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
