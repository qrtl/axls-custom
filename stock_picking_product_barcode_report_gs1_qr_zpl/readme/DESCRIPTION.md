This module prints the stock identification label of
`stock_picking_product_barcode_report_gs1_qr` as ZPL, so that a label printer
produces it directly instead of a sheet of A4 going through a laser printer.

Everything on the label is the same, and deliberately so: the same internal
reference, product name, purchase order, analytic account, lot/serial and shelf,
around the same GS1 payload built by the same code. The two modules are meant to
be installed side by side and compared on real stock before one of them is kept.

Only the output differs.

|  | sheet | ZPL |
| --- | --- | --- |
| Report | Stock QR Label (A4) | Stock QR Label (ZPL) |
| Media | A4, 40 labels of 47mm x 29mm | a roll of 47mm x 29mm labels |
| Printer | any PDF printer | a ZPL printer (a Zebra ZD421 here) |
| Produces | one PDF of whole sheets | one `^XA`...`^XZ` block per label |

The label is laid out in printer dots rather than in millimetres: 47mm x 29mm at
203dpi is 376 x 232 dots, and the template carries the arithmetic in comments so
the layout can be moved without re-deriving it.

**This module does not depend on Direct Print.** The report is a `qweb-text`
report, which is all it takes: where `printnode_base` is installed and a printer
is configured, it sends the stream to that printer as raw data, and where it is
not, the same action downloads the stream. That keeps the choice between the two
label modules free of the question of whether the purchased module is kept, and
it is how the layout can be checked without the printer on the desk.

**The stream is cp932, not UTF-8.** `^CI15` selects the printer's Shift-JIS
character set, so the report declares `cp932` through `report_text_format_option`
rather than leaving it to be set by hand on the report record afterwards. An
installation that misses this prints mojibake for every Japanese value on the
label, and nothing in the log says why.
