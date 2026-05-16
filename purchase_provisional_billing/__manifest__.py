# Copyright 2025 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Purchase Provisional Billing",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Purchase",
    "license": "AGPL-3",
    "depends": ["purchase_stock"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/purchase_order_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
