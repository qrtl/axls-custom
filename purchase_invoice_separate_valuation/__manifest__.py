{
    'name': 'Purchase Invoice Separate Valuation',
    'version': '16.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Separate purchase invoicing from stock valuation',
    'description': """
Purchase Invoice Separate Valuation
===================================

This module separates purchase invoicing from stock valuation:

* Allow multiple invoices creation without updating qty_invoiced
* Prevent vendor bill price adjustments from affecting stock.valuation.layer
* Add "Final Invoice" flag in invoice wizard
* Update purchase order status only when Final Invoice is confirmed
    """,
    'depends': [
        'purchase',
        'purchase_stock',
        'stock_account',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/account_move_reversal_views.xml',
        'views/account_move_views.xml',
        'views/purchase_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
