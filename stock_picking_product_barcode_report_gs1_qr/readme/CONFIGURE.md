Under *Inventory / Configuration / Settings / Barcode format*:

- **Default template for barcode labels** — set it to `Stock QR Label (A4)` so
  that the sheet is the one offered by default. The A4 sheet packs 40 of the
  47mm x 29mm labels, four across and ten down.
- **Analytic plan shown on stock labels** — the label prints the analytic
  account of this plan that the lot is distributed to (`stock_lot_analytic`
  copies the distribution from the receipt onto the lot). Leave it empty to omit
  that line.
- **Method to choose the barcode formating** — set it to
  `Display GS1 QR format for barcodes` to make the QR the default symbology on
  the base module's own label as well.

The purchase order shown on the label comes from `stock_lot_purchase_attribute`,
which stamps the lot when the receipt is validated.

Scanning needs `stock_barcodes_gs1` installed and the company's barcode
nomenclature set to a GS1 one. This module's AI (240) rule is added to
*Default GS1 Nomenclature*; a hand-built nomenclature needs its own copy of the
rule.
