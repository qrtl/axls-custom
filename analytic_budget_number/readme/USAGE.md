The budget number of a purchase order line is kept up to date with its analytic
distribution, and it falls back to the next budget account of the distribution
when the account it stands for is deleted.

It is not recomputed when the configuration behind it changes, though. That
covers every one of:

- another analytic plan is marked as the budget plan;
- an analytic account is moved into or out of the budget plan;
- a plan is grafted under the budget plan as a subplan, or moved out of it;
- the company of the budget plan changes.

After any of those changes, select the target lines in a list of purchase order
lines and choose *Recompute Purchase Line Budget* from the *Action* menu. Odoo
has no menu over the purchase order lines of its own; the OCA module
`purchase_order_line_menu` adds one under *Purchase > Orders*. Selecting every
line of the list is what brings all the budget numbers back in step, so use
*Select all* rather than the current page when the change affects the whole
history.

The action rewrites values that were stored against the configuration in place
at the time, so it is reserved to the *Settings* group.
