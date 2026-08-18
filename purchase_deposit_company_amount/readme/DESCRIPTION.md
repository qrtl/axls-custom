This module does the following:

- Adds a Company Currency Amount field to the deposit line of a vendor
  bill, which forces the line's balance to the amount entered instead of
  converting the foreign currency amount at the exchange rate.
- Carries the company currency value of a posted deposit bill over to the
  deposit offset line of the final bill, so the deposit account closes out
  at the amount that was actually paid.
- Books the resulting exchange rate difference into the product lines, and
  reflects it in the stock valuation of the received goods.

The field is only available on the deposit line of a vendor bill taking
part in a purchase deposit flow. Elsewhere the standard rate conversion
applies.

## Background:

When a purchase order is in a foreign currency, the deposit is usually
settled for an exact company currency amount that does not match the
exchange rate configured for that day. Odoo books the deposit at the rate,
so the deposit account never closes out cleanly against what was paid.

A paid deposit is a non-monetary asset, so the goods are measured at the
deposit's own rate for the prepaid portion and at the current rate for the
remainder. The difference is part of the acquisition cost rather than an
exchange gain or loss, which is why it is booked into the product lines.
