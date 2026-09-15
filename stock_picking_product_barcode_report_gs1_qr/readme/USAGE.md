The label sheet prints from the *Print* menu of any of these:

- **A receipt**, to label goods as they arrive. Every move line of the picking
  gets a label; the location printed is the destination of the move.
- **Physical inventory (quants) or lots**, to label a specific selection.

The wizard lists what will be printed, with the shelf, location, purchase order
and analytic account it resolved for each line, and a *Quantity of Labels*
column to print more than one copy.

The sheet sets the internal reference and the product name at 12pt, and the
purchase order, analytic account, lot and shelf at 10pt. 10pt is as large as
those four go: they have to hold the longest values the data carries, the
analytic account and the shelf take two lines each at that size, and the block
then fills the 63.5mm x 38.1mm cell. The block is centred in the cell so that a
sheet fed slightly off still lands the whole label inside its die cut.

The product name is the one field that can outrun its line whatever the size, so
it is printed from the start and cut on the right. 12pt was chosen against the
names actually held: of the products with stock, 92% print in full at that size,
against 96% at 10.5pt and 81% at 14pt.
A lot number or an internal reference near the GS1 maximum (20 and 30
characters) does not fit: the data here runs to 10 and 8, but a label built at
those limits loses its last line. Size, not room, is what decides this —
the line has space for 16pt, but a name would then print in full only 64% of the
time.

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
