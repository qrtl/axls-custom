The label sheet prints from the *Print* menu of any of these:

- **A receipt**, to label goods as they arrive. Every move line of the picking
  gets a label; the location printed is the destination of the move.
- **Physical inventory (quants) or lots**, to label a specific selection.
- **A location**, to reprint every label for a shelf in one go. Every quant
  stored anywhere below the selected locations is included.

The wizard lists what will be printed, with the location, purchase order and
analytic account it resolved for each line, and a *Quantity of Labels* column to
print more than one copy.

A line whose internal reference cannot be encoded — because it is empty, or
contains characters outside the GS1 alphanumeric set — still prints its text,
but without a QR code, which is how bad reference data shows up.
