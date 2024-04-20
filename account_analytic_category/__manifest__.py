# Copyright 2024 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Account Analytic Category",
    "version": "16.0.1.0.0",
    "category": "Accounting",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_analytic_category_views.xml",
        "views/account_analytic_plan_views.xml",
    ],
    "installable": True,
}
