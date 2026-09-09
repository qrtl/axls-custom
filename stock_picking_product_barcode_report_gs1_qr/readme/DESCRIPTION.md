`stock_picking_product_barcode_report` can print the product and the lot as a
single GS1-128 barcode, which `stock_barcodes_gs1` reads in one scan. At the
47mm x 29mm label size the module ships with, however, that barcode does not
fit: a `(02)GTIN(10)LOT` payload needs about 200 Code 128 modules, which leaves
an X-dimension of roughly 0.20mm, below the 0.250mm GS1 minimum, and a 203dpi
label printer cannot render it legibly.

This module adds a `Display GS1 QR format for barcodes` option next to the
existing GS1-128 one. It encodes the same `(02)GTIN(10)LOT` payload, so nothing
changes on the reading side, but as a QR code it decodes down to about 12mm
square and therefore fits the standard label with room to spare.

Set it on the printing wizard, or as the company default under
Inventory / Configuration / Settings / Barcode format.

A 2D imager is required: a laser scanner cannot read a QR code.
