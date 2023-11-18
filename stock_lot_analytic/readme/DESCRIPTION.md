This module does the following:

- Adds analytic distribution field to stock.lot and stock.quant models
  (by inheriting analytic.mixin).
- Assigns analytic distribution to created lots/serials (and quants)
  upon purchase receipt (analytic distribution is taken from the
  purchase order line).

Note that analytic distribution should be maintained in stock.lot,
although you could directly update it in stock.quant (and have it
reflected in stock.lot via the relation). When stock.quant record does
not have a lot/serial assigned to it, assigning analytic distribution to
this record will not persist when the quant is transfered to another
location.

## Background:

The module was created in a bid to facilitate the inventory analysis
based on the responsible project/department.

Products that are subject to this inventory analysis should be set for
lot/serial tracking.
