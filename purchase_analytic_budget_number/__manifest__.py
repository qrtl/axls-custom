# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Purchase Analytic Budget Number",
    "summary": "Show the budget number of a purchase order line as a field of "
    "its own, and keep it out of the analytic distribution of the order header",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Purchase",
    "license": "AGPL-3",
    "maintainers": ["nobuQuartile"],
    "depends": [
        "analytic_budget_number",
        "purchase_analytic",
        "purchase_order_line_menu",
    ],
    "data": [
        "data/server_action.xml",
        "views/purchase_order_line_views.xml",
        "views/purchase_order_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
