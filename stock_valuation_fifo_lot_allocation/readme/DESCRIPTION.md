For FIFO products tracked by lot/serial number, this module persists one record
every time a stock valuation layer is created, capturing how much of that
layer's value and quantity is charged to each lot.

`stock_valuation_fifo_lot` already produces the correct per-lot remaining value
on the stock move line, but it only exposes the current balance. Landed costs,
vendor bill price differences and revaluations leave no per-lot trace, so there
is no way to explain how a lot arrived at its value. This module records the
split at the moment the layer is created, while the information needed to split
it is still available, so that at audit time you can list, group and drill down
into exactly why each lot carries the value it does.

Each allocation row carries an amount and a quantity (in the product UoM, signed
as the layer quantity), so that it fully shadows the per-lot layer Odoo would
create if it valued lots natively:

- incoming layers: the lot's received quantity (`qty_base`), and the value
  prorated on it;
- outgoing layers: the quantity and value the FIFO run consumed from the lot
  (the increase of `qty_consumed` and `value_consumed` on the lot's incoming
  move lines);
- value-only layers (landed cost, price difference, revaluation): no quantity,
  and the value prorated on the remaining quantity of the lots in scope.

The ledger satisfies the following invariants, which the *Check Integrity*
action verifies:

- per layer, the allocations add up to the layer value;
- per lot, the allocations add up to the lot's remaining value
  (`stock.move.line.value_remaining`).

## Bridge to core lot valuation (18.0+)

Odoo 18.0 values lots natively (*Valuation by Lot/Serial number* on the product,
with a lot on each stock valuation layer). This module is a 16.0 bridge to that
model and is not meant to be migrated as such: at upgrade, it is replaced by
converting each allocation row into a per-lot valuation layer (lot, quantity =
`allocated_quantity`, value = `allocated_amount`) in place of the aggregate
layer it belongs to. Opening adjustment rows become value-only per-lot layers.
The invariants above are what make that conversion lossless, and should be
checked before upgrading.
