The analytic distribution of a purchase order line is held in a json field,
which cannot be shown as a column, grouped or filtered on. What a whole order
is distributed to is harder still to get to: an order level distribution can
only stand for the lines as long as every one of them is distributed the same
way, and it says nothing as soon as one line differs.

This module holds the analytic accounts of the lines on the order itself, so
they can be seen from the purchase order list.

## What it adds

On the purchase order:

- **Analytic Accounts of Lines** — the analytic accounts the lines of the order
  are distributed to. It holds the accounts of every line, whichever analytic
  plan they belong to, so the order still shows what it is distributed to when
  its lines are distributed differently.

The field is an optional column of the purchase order list, where the accounts
are shown as tags coloured by their analytic plan, the way the analytic
distribution itself is. It is stored, so the search view of the purchase order
searches orders by the name of an analytic account as well.

An account that is archived is kept on the order, so it is there again as soon
as it is unarchived. An account that is deleted leaves the order, as the
analytic distribution it stays behind in holds no reference to it.
