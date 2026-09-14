# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Picking Product Barcode Report GS1 QR ZPL",
    "summary": "Print the GS1 QR stock label as ZPL on a label printer",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Inventory",
    "license": "AGPL-3",
    "maintainers": ["nobuQuartile"],
    "depends": [
        "report_text_format_option",
        "stock_picking_product_barcode_report_gs1_qr",
    ],
    "data": [
        "report/report_stock_qr_label_zpl.xml",
        "report/report_stock_qr_label_zpl_template.xml",
    ],
    "installable": True,
}
