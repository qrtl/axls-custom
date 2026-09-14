The label sheet prints from the *Print* menu of any of these:

- **A receipt**, to label goods as they arrive. Every move line of the picking
  gets a label; the location printed is the destination of the move.
- **Physical inventory (quants) or lots**, to label a specific selection.
- **A location**, for everything stored anywhere below it. Note that this is the
  stock location, not the shelf printed on the label: where locations are
  warehouse-wide, selecting one takes in the whole warehouse.

The wizard lists what will be printed, with the shelf, location, purchase order
and analytic account it resolved for each line, and a *Quantity of Labels*
column to print more than one copy.

*Start at Label* fills up a sheet that has already had labels taken off it. Cells
are counted left to right and top to bottom, so 4 is the leftmost cell of the
second row: the printing then leaves the first three cells blank and carries on
from there. It applies to the first sheet only; any further sheet is printed
whole.

A line that cannot carry a code — no internal reference, or a reference or lot
number holding characters outside the GS1 alphanumeric set — is listed with the
reason in a *Cannot Be Printed* column, and Print raises rather than producing
the sheet. Fix the record, or drop the line by setting its label quantity to
zero, and print again.
