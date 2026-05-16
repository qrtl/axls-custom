# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Purchase Deposit Separate Valuation",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Purchase",
    "license": "AGPL-3",
    "summary": "Per-PO stock valuation freeze on top of purchase_deposit "
    "so vendor bills do not create price-difference SVL entries; any "
    "Stock-Input residual is closed out to a configurable adjustment "
    "account.",
    "depends": ["purchase_deposit", "purchase_stock"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/purchase_order_views.xml",
    ],
    "installable": True,
}
