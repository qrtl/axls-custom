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

1. **`Company Currency Amount` field on deposit lines only.**
   - Optional column in the vendor-bill line tree.
   - **Editable only on deposit lines** (where the underlying PO line
     has ``is_deposit = True``). Read-only on regular product / tax /
     AP lines for safety. The scope can be widened later if needed.
   - Leave blank to use the standard rate-based conversion.
   - Enter a value to force the deposit line's ``balance``
     (debit/credit) to that company-currency amount. The foreign
     currency ``amount_currency`` stays at ``price_unit × quantity``;
     only the company-currency side is replaced.
   - The companion AP / payable line is auto-balanced by Odoo from
     the remaining lines, so the journal still nets to zero.

2. **Deposit → final invoice propagation.**
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

3. **Deposit-line scope only (initial release).** The override is
   intentionally restricted to deposit lines. If a future requirement
   needs direct override on regular product lines of the final
   invoice, remove the ``is_deposit_line`` gate in
   ``_apply_company_amount_override`` and the corresponding
   ``readonly`` attribute on the view.

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

Standard "Create Bill" on the PO:
  → Final invoice in USD:
      Product line:        $100   company_amount = ¥11000 (auto rate)
      Deposit offset:     -$30    company_amount = -¥4000 (propagated)
      AP line:            -$70    balance       = -¥7000  (auto-balanced)
  → Optionally, the user can further override company_amount on the
    product line of the final invoice (e.g. ¥10800 instead of the
    rate-based ¥11000).
```

The user pays ¥4000 to the deposit bill and ¥7000 (or whatever the
USD $70 actually settles at) to the final bill. Exchange-rate
differences at payment time are recorded in Odoo's standard
exchange-diff journal.

## Notes

- A ``company_amount`` of zero / empty is treated as "no override" —
  Odoo's rate-based conversion applies as usual.
- The override only affects the line it's set on; AP and tax lines
  are auto-balanced and do not need a separate override.
- Tax-exclusive vs tax-inclusive behaviour is unchanged: the foreign
  currency total (and tax computation) is still driven by
  ``price_unit × quantity``.
