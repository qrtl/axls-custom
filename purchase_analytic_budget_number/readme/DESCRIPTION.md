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

## What it keeps apart

`purchase_analytic` puts an analytic distribution on the purchase order itself:
setting it applies it to every line of the order at once, and the header shows
what the lines have in common. A budget number stands for a single line, so the
two have nothing to do with each other, and this module keeps the budget number
out of the header:

- the budget plan is unavailable on the header, so the widget there neither
  offers a budget number nor shows one;
- applying the distribution of the header to the lines carries over the budget
  number of each line instead of overwriting it, which is what the plain write
  of the distribution would do;
- the header reads the lines with their budget numbers left out, so lines that
  differ by nothing else still show their common distribution there.

The header is told apart from the lines by the business domain its field passes
to the analytic distribution widget, `purchase_order_header`, which the
applicability of the plan is read against. The lines pass `purchase_order`, as
Odoo has them do.

This module is installed automatically once the modules it depends on are.
