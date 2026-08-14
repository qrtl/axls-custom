# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Purchase Deposit Multi-Currency",
    "version": "16.0.3.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Purchase",
    "license": "AGPL-3",
    "summary": "Let vendor-bill lines in a purchase-deposit flow carry a "
    "manually-entered company-currency amount so foreign-currency deposits "
    "and invoices post the exact JPY (company-currency) value the user "
    "actually paid, bypassing Odoo's exchange-rate conversion. The deposit "
    "value is carried over to the deposit-offset line of the final invoice.",
    # purchase_stock: the override drives the price-difference / SVL logic
    # through ``_get_gross_unit_price``, which only exists once stock
    # valuation is in play.
    "depends": ["purchase_deposit", "purchase_stock"],
    "data": [
        "views/account_move_views.xml",
    ],
    "installable": True,
}
