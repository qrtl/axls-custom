# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Move Ingore Last Purchase Date",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Product",
    "license": "AGPL-3",
    "depends": ["product_last_purchase_date"],
    "data": [
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
    ],
    "installable": True,
}
