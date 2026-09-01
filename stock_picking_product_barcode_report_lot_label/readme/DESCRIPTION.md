The product barcode label of `stock_picking_product_barcode_report` prints the
lot/serial number as plain text only, so a warehouse operator has to key it in
by hand when the label is scanned.

This module adds a second, scannable Code128 barcode carrying the lot/serial
number underneath the product barcode, on labels that have a lot/serial number
assigned.

Labels printed in GS1-128 format are left untouched: that barcode already
carries the lot in application identifier `(10)`, so a second symbol would only
duplicate it.
