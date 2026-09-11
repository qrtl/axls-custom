This module prints a label that identifies a specific piece of stock, so that an
inventory count can be done by scanning rather than by keying references in.

The label carries the internal reference, the product name, the purchase order,
an analytic account, the lot/serial number and the location the stock is
currently in, next to a QR code that encodes the product and the lot as a single
GS1 payload. `stock_barcodes_gs1` resolves both from one scan, so a count is
"scan the shelf, then scan each item".

Two things about the encoding are worth knowing.

**Why QR rather than GS1-128.** `stock_picking_product_barcode_report` can
already print the product and the lot as one GS1-128 barcode, but that payload
needs about 200 Code 128 modules. On the 47mm x 29mm label the base module ships
that leaves an X-dimension of roughly 0.20mm, below the 0.250mm GS1 minimum, and
a 203dpi label printer cannot render it legibly. The same payload as a QR code
decodes down to about 12mm square.

**Why AI (240) and not AI (02).** AI (02) carries a GTIN, which most
manufactured-part catalogues simply do not have. The label therefore falls back
to AI (240), "additional product identification assigned by the manufacturer",
which `stock_barcodes_gs1` resolves against the product's internal reference.
AI (240) is variable length, so the payload separates it from the lot element
with `#` — the FNC1 stand-in that `barcode.nomenclature` accepts out of the box,
and which a keyboard-wedge scanner can actually transmit. Odoo ships no rule for
AI (240), so this module adds one to the default GS1 nomenclature.

Products that do carry a GTIN keep the standard `(02)GTIN(10)LOT` payload.

A 2D imager is required: a laser scanner cannot read a QR code.
