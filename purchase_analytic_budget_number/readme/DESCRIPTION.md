The budget number of a purchase order line is hard to get to: it is held in the
analytic distribution, a json field that cannot be grouped or filtered on.

This module exposes it as a field of its own.

## What it adds

On the purchase order line:

- **Analytic Budget** — the account the line is distributed to within the plan
  marked as the budget plan by `analytic_budget_number`, or within one of its
  subplans. It is stored, so the purchase order lines can be grouped and
  filtered by budget number. Should the line be distributed to several accounts
  of that plan, the oldest of them is taken, as the analytic distribution keeps
  them in no meaningful order. Only the accounts of the company of the line are
  considered, which matters when the budget plan is shared by every company.

The field becomes a column of the purchase order line list and a field and a
group-by of its search view. Odoo has no menu over the purchase order lines of
its own, so the list is reached through the one the OCA module
`purchase_order_line_menu` adds under *Purchase > Orders*.

The budget number is only shown to a user of the *Analytic Accounting* group, as
an analytic account is of no use to anyone else.

This module is installed automatically once the modules it depends on are.
