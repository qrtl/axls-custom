Go to *Inventory > Reporting > Lot Valuation Allocation*.

The list is grouped by lot/serial number and ordered by actual date. Each line
drills through to the valuation layer it comes from, and the group totals equal
the lot's remaining value and quantity. The pivot view breaks the allocated
amount and quantity down by lot and period.

## Historical layers

On installation, a scheduled action backfills the valuation layers that already
exist. It processes one batch per run, newest first, re-triggering itself until
the backlog is drained, and then idles, setting the system parameter
`stock_valuation_fifo_lot_allocation.backfill_before_id` to `-1`. Layers that
already have allocations are skipped, so deleting that parameter fills in
whatever is missing on the next run; to rebuild the ledger from scratch, delete
the allocation records and the parameter.

Past FIFO runs are not recorded per layer, so the backfill reconstructs them:

- incoming layers: as above, exact;
- outgoing layers: a lot received once is charged its delivered quantity at the
  rate of its receipt line (`value_consumed / qty_consumed`), and the lots
  received several times (e.g. through a lot revaluation) share the rest of the
  layer value, prorated on their quantity;
- value-only layers: prorated on what the lots held when the layer was posted,
  that is their current remaining quantity plus what later deliveries took from
  them. A lot received several times keeps its current remaining quantity, as
  which receipt the later deliveries drew on is not known.

This is exact as long as no value (landed cost, price difference, revaluation)
landed on a receipt after its first delivery, and, for a value-only layer or a
delivery of several such lots, the lots were received only once; other cases
are approximated. Once the backlog is drained, a single *Opening allocation
adjustment* record per lot absorbs whatever difference is left, so the
invariants hold exactly and every approximation stays visible in one auditable
row. Adjustment rows carry no quantity.

## Forced FIFO lots

When a *Force FIFO Lot/Serial* is set on an outgoing move line, the ledger
charges the lot whose FIFO balance was consumed, not the lot physically shipped.
This is what keeps the ledger consistent with the valuation.
