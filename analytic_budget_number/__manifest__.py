# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Analytic Budget Number",
    "summary": "Search analytic accounts by subsystem, component and model, and "
    "show them as the budget number of purchase order lines",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Analytic",
    "license": "AGPL-3",
    "maintainers": ["nobuQuartile"],
    "depends": ["analytic", "purchase"],
    "data": [
        "data/server_action.xml",
        "views/account_analytic_account_views.xml",
        "views/account_analytic_plan_views.xml",
    ],
    "installable": True,
}
