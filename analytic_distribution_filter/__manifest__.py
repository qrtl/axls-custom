# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Analytic Distribution Filter",
    "version": "16.0.1.0.0",
    "category": "Analytic",
    "website": "https://www.quartile.co",
    "author": "Quartile",
    "license": "AGPL-3",
    "depends": ["analytic"],
    "data": [
        "security/ir.model.access.csv",
        "views/analytic_account_views.xml",
        "views/ir_model_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "analytic_distribution_filter/static/src/js/analytic.esm.js",
        ],
    },
    "installable": True,
}
