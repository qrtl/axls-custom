# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Analytic Budget Number",
    "summary": "Record the satellite, subsystem, component and model of an "
    "analytic account and mark the analytic plan that holds the budget numbers",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Analytic",
    "license": "AGPL-3",
    "maintainers": ["nobuQuartile"],
    # account, as the menus the master data of the attributes is maintained
    # from sit under the Analytic Accounting section it holds.
    "depends": ["account", "analytic"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_analytic_account_views.xml",
        "views/account_analytic_plan_views.xml",
        "views/analytic_budget_attribute_views.xml",
    ],
    "installable": True,
}
