# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Lot Suffix",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "",
    "license": "AGPL-3",
    "depends": ["purchase", "stock", "analytic_mixin_analytic_account"],
    "data": [
        "views/account_analytic_account_views.xml",
        "views/stock_lot_views.xml",
        "views/purchase_order_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
