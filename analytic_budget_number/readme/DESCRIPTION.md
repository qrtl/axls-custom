An analytic account can only be found by its name or its code. That is a poor
fit when the accounts of a plan stand for budget numbers: people remember which
subsystem, which component and which model a budget is for, but rarely the
number itself.

This module records those three attributes on the analytic account, makes each
of them a way to find it, and marks the analytic plan whose accounts stand for
budget numbers.

## What it adds

On the analytic account:

- **Subsystem** — free text
- **Component** — free text
- **Model** — EM / FM / Racksat

The three attributes appear on the analytic account form, as optional columns of
the list, and in the search view as both fields and group-bys.

On the analytic plan:

- **Use for Budget Numbers** — the accounts of the plan, and of its subplans,
  stand for budget numbers. One plan at most per company, so that a record
  distributed to analytic accounts has a single budget number.

The flag carries no behaviour of its own: it is what the modules exposing the
budget number of a record read to tell the budget accounts of its analytic
distribution from the rest. `purchase_analytic_budget_number` does so for the
purchase order lines.
