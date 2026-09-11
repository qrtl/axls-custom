The label sheet prints from the *Print* menu of any of these:

- **A receipt**, to label goods as they arrive. Every move line of the picking
  gets a label; the location printed is the destination of the move.
- **Physical inventory (quants) or lots**, to label a specific selection.
- **Shelf information**, to reprint a whole shelf in one go. Filter or group
  *Inventory / Products / Shelf Information* by area, select the rows, and every
  quant sitting on those shelves is included.
- **A location**, for everything stored anywhere below it. Note that this is the
  stock location, which is often warehouse-wide — the shelves above are usually
  the selection you want.

The wizard lists what will be printed, with the shelf, location, purchase order
and analytic account it resolved for each line, and a *Quantity of Labels*
column to print more than one copy.

A line whose internal reference cannot be encoded — because it is empty, or
contains characters outside the GS1 alphanumeric set — still prints its text,
but without a QR code, which is how bad reference data shows up.
