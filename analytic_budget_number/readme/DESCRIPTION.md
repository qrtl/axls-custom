An analytic account can only be found by its name or its code. That is a poor
fit when the accounts of a plan stand for budget numbers: people remember which
satellite, which subsystem, which component and which model a budget is for,
but rarely the number itself.

This module records those attributes on the analytic account and makes each of
them a way to find it, adds a free-text description of what the budget number
is for, and marks the analytic plan whose accounts stand for budget numbers.

## What it adds

On the analytic account:

- **Satellite**
- **Subsystem**
- **Component**
- **Model**
- **Budget Description** — free text, what the budget number is for

The attributes are master data of their own, one model each, so that an account
is given a value that is already in use rather than one retyped on it. They
appear on the analytic account form, as optional columns of the list, and in the
search view as both fields and group-bys. The description appears on the form
and as a column of the list, shown by default. On the form they are only shown
on the accounts of the budget plan described below, as they mean nothing on any
other account.

The list of the analytic accounts is what an account is looked up in, budget
numbers included, and there the attributes say more about a budget number than
the reference and the customer do. Both become optional columns, hidden by
default, and the description takes their place, next to the attributes.

On the analytic plan:

- **Use for Budget Numbers** — the accounts of the plan, and of its subplans,
  stand for budget numbers. One plan at most per company, so that a record
  distributed to analytic accounts has a single budget number.

The flag carries no behaviour of its own: it is what the modules exposing the
budget number of a record read to tell the budget accounts of its analytic
distribution from the rest. `purchase_analytic_budget_number` does so for the
purchase order lines.
