# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Purchase Deposit Company Amount",
    "summary": "Book purchase deposits at the company-currency amount actually paid",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Purchase",
    "license": "AGPL-3",
    "maintainers": ["kanda999"],
    # purchase_stock: holds the price-difference logic that consumes
    # ``_get_gross_unit_price`` (which is itself defined in stock_account) and
    # writes the stock valuation adjustment the override has to reach.
    "depends": ["purchase_deposit", "purchase_stock"],
    "data": [
        "views/account_move_views.xml",
    ],
    "installable": True,
}
