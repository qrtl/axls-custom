The budget number is read from the analytic plan flagged as the budget plan, so
a purchase order line carries none until one is flagged. See the *Configuration*
section of `analytic_budget_number`.

## Making the budget number mandatory

The module ships an automated action, *Budget Number Required on Purchase Order
Lines*, that refuses a purchase order line carrying no budget number. It is off
by default. Turn it on from *Settings > Technical > Automation > Automated
Actions*, once the budget plan is flagged and the purchase order lines that
predate it carry a budget number of their own. Flag the plan first: with none
flagged no line carries a budget number, and the rule would refuse every one of
them.

The rule runs on the creation of a line and on an update that writes the
analytic distribution of one. Everything else a purchase order line is written
by — receiving the goods, billing them — is left alone, which is what keeps the
lines that predate the rule from blocking those flows. Taking the budget number
off a line that carries one is only caught on the next write of its
distribution.

An update of the module leaves the rule the way you left it, on or off.
