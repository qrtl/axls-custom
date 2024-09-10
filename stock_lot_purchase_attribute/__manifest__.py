# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Lot Purchase Attribute",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": ["purchase_stock"],
    "data": [
        "data/ir_cron.xml",
        "views/stock_lot_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_quant_views.xml",
    ],
    "installable": True,
}
