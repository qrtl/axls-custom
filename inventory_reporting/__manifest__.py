# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Inventory Reporting",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Reporting",
    "license": "AGPL-3",
    "depends": [
        "mrp_subcontracting",
        "analytic_mixin_analytic_account",
        "product_last_purchase_date",
        "report_xlsx",
        "stock_analytic",
        "stock_valuation_layer_accounting_date",
        "stock_picking_accounting_date",
        "web_ir_actions_act_multi",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/inventory_report_wizard_views.xml",
        "reports/inventory_report.xml",
        "views/product_category_views.xml",
    ],
    "installable": True,
}
