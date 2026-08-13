An analytic account can only be found by its name or its code. That is a poor
fit when the accounts of a plan stand for budget numbers: people remember which
subsystem, which component and which model a budget is for, but rarely the
number itself. The budget number of a purchase order line is just as hard to
get to, as it is held in the analytic distribution, a json field that cannot be
grouped or filtered on.

This module records those three attributes on the analytic account, makes each
of them a way to find it, and exposes the budget number of a purchase order
line as a field of its own.

## What it adds

On the analytic account:

- **Subsystem** — free text
- **Component** — free text
- **Model** — EM / FM / Racksat

The three attributes appear on the analytic account form, as optional columns of
the list, and in the search view as both fields and group-bys.

On the purchase order line:

- **Analytic Budget** — the account the line is distributed to within the plan
  marked as the budget plan, or within one of its subplans. It is stored, so
  the purchase order lines can be grouped and filtered by budget number. Should
  the line be distributed to several accounts of that plan, the oldest of them
  is taken, as the analytic distribution keeps them in no meaningful order. Only
  the accounts of the company of the line are considered, which matters when the
  budget plan is shared by every company.
