# Purchase Provisional Billing

Implements a provisional billing flow for purchase orders where vendor bills
can be issued and paid before the final, product-linked vendor bill is
created.

## Flow

1. Enable **Separate Valuation Mode** on the purchase order.
2. Receive goods normally; stock valuation is posted against GRNI at receipt
   as in standard Odoo.
3. Create one or more **Advance Bills** from the PO. Advance bills carry no
   product link (so `qty_invoiced` and stock valuation are not affected) and
   use the line's expense account.
4. When an Advance Bill is **posted**, the module automatically creates and
   posts a paired **Application Credit Note** that mirrors the Advance Bill
   line-for-line. The pair has zero net P&L impact, but the credit note's
   payable line remains open, waiting to be reconciled with the Final Bill.
5. The Advance Bill itself is paid through the normal payment workflow.
6. Once all items have been received and all Advance Bills are posted, click
   **Create Final Bill** on the PO. This creates a *standard* Odoo vendor
   bill — product-linked, updating `qty_invoiced`, going through the normal
   GRNI / price-difference flow.
7. When the Final Bill is **posted**, the module automatically:
   - Computes the residual difference between the Final Bill's payable line
     and the sum of the paired credit notes' payable lines.
   - If non-zero, posts a **Settlement Adjustment** journal entry whose
     payable line offsets the residual.
   - Reconciles the Final Bill, the Application Credit Notes, and (if any)
     the Adjustment entry's payable line together — closing out the Final
     Bill as fully paid.

## Why this design

Advance bills are kept as plain, product-less vendor bills so that the
"per-unit cost" reflected in `qty_invoiced` and any reporting that depends on
it is driven only by the Final Bill (which uses the PO price and updates
stock valuation through Odoo's standard price-difference logic). Differences
between what was actually paid (advance bills) and the PO/receipt value are
absorbed in a dedicated adjustment account, keeping the rest of the
accounting in line with stock movements.

## Configuration

Go to **Accounting > Configuration > Settings > Separate Valuation Mode**:

- **Settlement Adjustment Account**: The account used to absorb the
  difference between the Final Bill amount and the sum of paired credit
  notes when the Final Bill is settled.
