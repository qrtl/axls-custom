{
    'name': 'Purchase Invoice Separate Valuation',
    'version': '16.0.2.0.0',
    'category': 'Purchase',
    'summary': 'Separate purchase invoicing from stock valuation',
    'depends': [
        'purchase',
        'purchase_stock',
        'stock_account',
        'account',
        'stock_landed_costs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/purchase_make_invoice_advance_views.xml',
        'views/account_move_views.xml',
        'views/purchase_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
