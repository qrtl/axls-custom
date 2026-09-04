# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Analytic Budget Number",
    "summary": "Record the subsystem, component and model of an analytic account "
    "and mark the analytic plan that holds the budget numbers",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Analytic",
    "license": "AGPL-3",
    "maintainers": ["nobuQuartile"],
    "depends": ["analytic"],
    "data": [
        "views/account_analytic_account_views.xml",
        "views/account_analytic_plan_views.xml",
    ],
    "installable": True,
}
