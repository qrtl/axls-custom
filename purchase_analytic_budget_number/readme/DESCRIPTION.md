`analytic_budget_number` exposes the budget number of a purchase order line as a
field of its own, but Odoo has no menu over the purchase order lines to show it
in. The OCA module `purchase_order_line_menu` adds one under *Purchase >
Orders*.

This module brings the two together: the budget number becomes a column of the
list that menu opens, and a field and a group-by of its search view. It is a
glue module, and it is installed automatically once both of the modules it
depends on are.

The budget number is only shown to a user of the *Analytic Accounting* group, as
an analytic account is of no use to anyone else.
