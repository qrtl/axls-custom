# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Lot Analytic",
    "summary": "Adds analytic distribution in lot",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": ["purchase_stock"],
    "data": [
        "views/stock_lot_views.xml",
        "views/stock_quant_views.xml",
    ],
    "installable": True,
}
