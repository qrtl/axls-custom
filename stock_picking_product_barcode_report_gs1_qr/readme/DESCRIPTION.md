This module prints a label that identifies a specific piece of stock, so that an
inventory count can be done by scanning rather than by keying references in.

The label carries the internal reference, the product name, the purchase order,
an analytic account, the lot/serial number and the shelf the stock sits on, next
to a QR code that encodes the product and the lot as a single GS1 payload.

The shelf is `product.shelfinfo`, not the stock location: an installation whose
locations are warehouse-wide keeps the shelf address there instead, and printing
the location would put the same string on every label. `stock_barcodes_gs1` resolves both from one scan, so a count is
"scan the shelf, then scan each item".

Two things about the encoding are worth knowing.

**Why QR rather than GS1-128.** `stock_picking_product_barcode_report` can
already print the product and the lot as one GS1-128 barcode, but the AI (240)
payload is variable length, and alphanumeric where a GTIN is not: the rule allows
a 30-character reference beside a 20-character lot, which is 640 Code 128 modules
and about 165mm at the 0.250mm GS1 minimum X-dimension. No 1D symbol that wide
goes on a 63.5mm x 38.1mm label, and one narrowed to fit is not rendered legibly
by a 203dpi label printer. The same payload as a QR code sits in a 20mm square
and leaves the rest of the label to the text a person reads.

**The product is always AI (240), never AI (02).** AI (02) carries a GTIN, which
most manufactured-part catalogues simply do not have. AI (240), "additional
product identification assigned by the manufacturer", carries the internal
reference instead, and `stock_barcodes_gs1` resolves it against `default_code`.
The product barcode is deliberately ignored even when one is set: AI (02)
validates a check digit, so a barcode that merely looks numeric makes the whole
payload fail to decompose — a label that looks finished and that no scanner can
read.

AI (240) is variable length, so the payload separates it from the lot element
with `#` — the FNC1 stand-in that `barcode.nomenclature` accepts out of the box,
and which a keyboard-wedge scanner can actually transmit. Odoo ships no rule for
AI (240), so this module adds one to the default GS1 nomenclature.

**Printing refuses rather than producing a label nothing can scan.** A product
with no internal reference, or a reference or lot number holding characters
outside the GS1 alphanumeric set, cannot be encoded. The wizard says so per line
and the Print button raises, naming every record to fix — a label that looks
complete but carries no usable code would otherwise be found out months later,
at the count it was printed for.

A 2D imager is required: a laser scanner cannot read a QR code.
