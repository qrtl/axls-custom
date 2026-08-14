# Purchase Deposit Multi-Currency

Adds a per-line **Company Currency Amount (会社通貨価格)** override on
vendor bills, plus automatic propagation of that value from a deposit
bill to the deposit-offset line of the final invoice.

## Why

When the purchase order is in a foreign currency, the user often pays
an exact JPY (company-currency) amount that does not match Odoo's
configured exchange rate at the deposit date. For example, paying
**¥4000** as a deposit on a **USD 100** purchase order, even though
USD 30 at today's rate would convert to ¥3300.

Odoo's standard behaviour would record ¥3300 in the journal (= $30 ×
rate). This module lets the user enter ¥4000 directly on the bill
line, regardless of the rate.

## What it does

1. **`Company Currency Amount` field on deposit-related vendor-bill lines.**
   - Optional column in the vendor-bill line tree (in_invoice /
     in_refund only).
   - **Scope: the purchase-deposit flow only.** The field is editable
     only on a move that carries a deposit line — i.e. the deposit
     vendor bill itself (positive deposit line) or the final invoice
     (negative deposit-offset line). On any other vendor bill it is
     read-only, and a value set there is rejected by a constraint.
     Outside the deposit flow Odoo's standard rate conversion applies,
     unchanged.
   - Leave blank to use the standard rate-based conversion.
   - Enter a value to force the line's ``balance`` (debit/credit) to
     that company-currency amount. The foreign currency
     ``amount_currency`` stays at ``price_unit × quantity``; only the
     company-currency side is replaced.
   - The companion AP / payable line is auto-balanced by Odoo from
     the remaining lines, so the journal still nets to zero.

2. **Stock valuation adjustment for product lines.**
   - When the overridden line is a stockable product valued in real
     time, the override also drives ``purchase_stock``'s price-diff
     logic. The hook is ``_get_gross_unit_price``: it returns a
     foreign-currency unit price that, divided by the date-based
     ``currency_rate``, yields exactly ``company_amount / quantity``.
   - As a result, both the price-difference AML (stock_in vs.
     expense) and the corresponding ``stock.valuation.layer``
     adjustment reflect the user-entered JPY value rather than the
     rate-converted one.

3. **Deposit → final invoice propagation.**
   - When a deposit vendor bill (created by ``purchase_deposit``'s
     *Register Deposit* wizard) is posted, its line's
     ``company_amount`` is captured and stored on the corresponding
     PO deposit line in a new ``deposit_company_amount`` field.
   - When the user later runs the standard "Create Bill" on the PO,
     ``purchase_deposit`` adds a negative-quantity offset line for
     the deposit; this module sets ``company_amount`` on that line
     to the negated stored value.
   - End result: the offset line's JPY balance exactly mirrors the
     deposit bill's JPY balance, so the deposit account closes out
     cleanly even when the exchange rate has moved between deposit
     posting and final invoice creation.

4. **Rate-difference absorbed by the product line(s).**
   - Because the offset line is pinned to the JPY actually paid while
     the product lines are booked at the *current* rate, there is a
     rate-difference (the deposit valued at today's rate vs. the JPY
     actually paid). This difference is part of the goods'
     acquisition cost, so the module pushes it onto the product
     line(s) via their ``company_amount`` (distributed proportionally
     when there is more than one).
   - End result: the product line reflects the **true cost**
     (deposit paid + remaining foreign amount × current rate), and
     the auto-balanced payable equals exactly the **remaining**
     foreign amount converted at the current rate.
   - The value is recomputed if the rate changes (e.g. the invoice
     date is edited) and never overwrites a ``company_amount`` the
     user entered manually on a product line.

## Example

```
PO (USD): 1 × $100
Receive: standard receipt at PO unit cost.

Register Deposit wizard (standard purchase_deposit, no changes):
  → Deposit bill in USD: 1 × $30
  → User overrides company_amount = 4000   (¥ direct input)
  → Post deposit bill
    Journal: Deposit account  debit  ¥4000  amount_currency  $30
             AP               credit ¥4000  amount_currency -$30
  → PO deposit line now stores deposit_company_amount = ¥4000

Standard "Create Bill" on the PO (current rate USD 1 = ¥160):
  → Final invoice in USD:
      Product line:        $100   company_amount = ¥15200 (auto adj.)
      Deposit offset:     -$30    company_amount = -¥4000 (propagated)
      AP line:            -$70    balance       = -¥11200 (auto-balanced)
  → Product line = ¥4000 (deposit paid) + $70 × 160 (¥11200) = ¥15200,
    i.e. the rate-difference (deposit at 160 = ¥4800 vs. ¥4000 paid =
    ¥800) is subtracted from $100 × 160 = ¥16000 → ¥15200.
  → The user may still override company_amount manually on the product
    line; a manual value is never overwritten by the auto adjustment.
```

The user pays ¥4000 to the deposit bill and ¥11200 (USD $70 at the
current rate) to the final bill. Exchange-rate differences at payment
time are recorded in Odoo's standard exchange-diff journal.

## Direct override on a product line

Within the deposit flow, a product line on the **final invoice** may
also be overridden by hand — e.g. the PO is USD 100 / qty 1 and the
user enters ``company_amount = ¥17000`` instead of the rate-converted
¥15000. ``_get_gross_unit_price`` makes the price-diff logic see the
JPY override:

```
Receipt SVL : qty 1, value ¥15000  (rate-based at receipt date)
Vendor bill : $100, company_amount = ¥17000
  Journal:  stock_in   debit  ¥15000
            expense    debit  ¥2000
            AP         credit ¥17000  amount_currency -$100
  SVL adj  : value +¥2000 on the receipt layer
```

The stock valuation now reflects the actual JPY paid. A manual value
is never overwritten by the deposit rate-difference adjustment.

On a vendor bill with no deposit line the field is read-only, so this
override is not available there.

## Notes

- A ``company_amount`` of zero / empty is treated as "no override" —
  Odoo's rate-based conversion applies as usual.
- The scope restriction is deliberate for the first release: the
  requirement is the purchase-deposit flow only. Extending the
  override to plain vendor bills would mean splitting the module so
  the generic part no longer depends on ``purchase_deposit``.
- The override only affects the line it's set on; AP and tax lines
  are auto-balanced and do not need a separate override.
- Tax-exclusive vs tax-inclusive behaviour is unchanged: the foreign
  currency total (and tax computation) is still driven by
  ``price_unit × quantity``.
