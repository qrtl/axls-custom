The analytic plan that supplies the 衛星名 line is the company setting of
`stock_picking_product_barcode_report_gs1_qr` (*Inventory / Configuration /
Settings / Barcode format*); this module reads the same one.

To print rather than download, `printnode_base` has to be installed and a
printer resolvable for the user — a workstation printer, a default printer on
the user, or a default printer on the company. No setting here points at a
printer: the report follows whatever Direct Print resolves for it, like every
other report.

The printer has to hold a Japanese font. `^CI15` selects its Shift-JIS character
set, and a printer without the font prints the Latin values and blanks the rest.
