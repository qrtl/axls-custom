# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Valuation Layer Reporting",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Reporting",
    "license": "AGPL-3",
    "depends": [
        "analytic_mixin_analytic_account",
        "product_last_purchase_date",
        "report_xlsx",
        "stock_analytic",
        "stock_move_actual_date",
        "web_ir_actions_act_multi",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/svl_report_category.xml",
        "wizards/svl_report_wizard_views.xml",
        "wizards/svl_report_category_wizard_views.xml",
        "reports/svl_report.xml",
        "views/product_category_views.xml",
        "views/stock_valuation_layer_views.xml",
        "views/svl_report_category_views.xml",
    ],
    "installable": True,
}
