# Purchase Deposit Separate Valuation

Per-PO stock-valuation freeze on top of OCA's `purchase_deposit`, with
automatic Stock-Input (GRNI) residual handling.

## What it does

When `Separate Valuation Mode` is enabled on a purchase order:

1. **Stock value stays at the receipt cost.** Vendor bills linked to the
   PO no longer create the price-difference SVL that standard Odoo
   posts when the billed amount differs from the receipt cost.
2. **The Stock-Input residual is closed automatically.** Because the
   SVL is suppressed, the Stock-Input (GRNI) account would otherwise
   carry the price difference as an open balance. After every vendor
   bill posts, the module recomputes the residual for the PO and posts
   (or replaces) a journal entry that closes the residual to the
   configured **Separate-Valuation GRNI Adjustment Account**.

The adjustment is computed and posted only once the PO is **fully
invoiced** (every stockable PO line's `qty_invoiced ≥ qty_received`),
so partial / deposit bills do not produce premature adjustments.

## Why

`purchase_deposit` gives a clean deposit + offset flow, but the final
invoice still goes through standard Anglo-Saxon accounting which moves
stock value via price-difference SVL whenever the bill amount differs
from the receipt cost. For workflows where stock valuation must stay
exactly at the receipt moment (so reporting figures are not disturbed
by billed amounts), this module turns that adjustment into a separate
journal entry against a dedicated account.

## Example

Receipt 1000, final vendor bill 1200 (Separate Valuation Mode enabled):

```
Receipt:         Stock 1000 / GRNI 1000
Vendor bill:     GRNI 1200 / AP 1200    (no SVL created)
GRNI adjustment: GRNI -200 / Adjustment +200   (auto-posted)

Net stock value: 1000 (unchanged)
Net GRNI:        0
Adjustment a/c:  +200 (loss recognised)
```

If a later bill changes the picture (refund, additional invoice, etc.),
the old adjustment entry is replaced with a fresh one reflecting the
new aggregate balance.

## Configuration

Settings → Accounting → *Purchase Deposit — Separate Valuation*:

- **Separate-Valuation GRNI Adjustment Account** — required. Expense
  account that absorbs the price difference.
- **Separate-Valuation GRNI Adjustment Journal** — optional. Defaults
  to the first General journal of the company.

Per purchase order, tick **Separate Valuation Mode** under *Invoicing*.

## Related

- For recording a deposit in a currency different from the PO
  currency, install the companion module **Purchase Deposit
  Multi-Currency** (`purchase_deposit_currency`).

## Notes / Limitations

- The adjustment is recomputed (delete + create) every time a vendor
  bill on the PO changes state. If the previous adjustment has been
  reconciled manually, removal raises an error and the user must
  unreconcile / reverse it first.
- The adjustment only fires after the PO is fully invoiced. Until
  then the Stock-Input residual is expected (and visible in reports);
  the freeze prevents stock movement but does not pre-emptively close
  GRNI on partial bills.
