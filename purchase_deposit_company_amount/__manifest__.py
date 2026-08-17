# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Purchase Deposit Company Amount",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Purchase",
    "license": "AGPL-3",
    "summary": "Book purchase deposits at the company-currency amount actually paid",
    "maintainers": ["kanda999"],
    # purchase_stock: the override feeds the price-difference / SVL logic that
    # consumes ``_get_gross_unit_price`` (defined in stock_account), which only
    # runs once stock valuation is in play.
    "depends": ["purchase_deposit", "purchase_stock"],
    "data": [
        "views/account_move_views.xml",
    ],
    "installable": True,
}
