Register the deposit with the standard *Register Deposit* wizard, and enter
the company currency amount actually paid in the Company Currency Amount
column of the deposit bill before posting it. The column is optional, and
can be shown from the bill line list.

Create the final bill from the purchase order as usual. The deposit offset
line is pinned to the amount entered on the deposit bill, and the exchange
rate difference is added to the product lines.

For a purchase order of USD 100 with a 30% deposit settled for JPY 3900,
where the rate on the final bill date is USD 1 = JPY 160:

    Product line      $100    15100
    Deposit offset    -$30    -3900
    Payable           -$70   -11200

The product line carries 3900 paid for the deposit plus USD 70 at the
current rate, and the payable is the remaining USD 70 at that rate.

The field is only editable on deposit lines, the deposit being the one
amount known outside Odoo. The goods lines follow from it automatically and
are read-only. Leave the field empty to keep the standard conversion.
