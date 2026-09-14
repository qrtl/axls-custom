Print from the same places as the sheet label — a receipt, quants, lots, shelf
information or a location — and pick **Stock QR Label (ZPL)** as the report.

A line that cannot be encoded is refused here exactly as it is for the sheet: the
wizard gives the reason per line in the *Cannot Be Printed* column, and the Print
button raises naming every record to fix.

To check the layout without a printer, leave Direct Print disabled (or clear the
printer) and print: the ZPL comes back as a file. Its labels can be rendered as
images by posting them to a ZPL rendering service — bear in mind that this sends
the label content to a third party, so use masked data rather than live stock.
