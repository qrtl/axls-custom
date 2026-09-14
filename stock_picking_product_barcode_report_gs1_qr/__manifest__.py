# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Picking Product Barcode Report GS1 QR",
    "summary": "Print a stock identification label carrying a GS1 QR code",
    "version": "16.0.1.1.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Inventory",
    "license": "AGPL-3",
    "maintainers": ["nobuQuartile"],
    "depends": [
        "barcodes_gs1_nomenclature",
        # Declares the cp932 encoding the ^CI15 ZPL label needs.
        "report_text_format_option",
        "stock_lot_analytic",
        "stock_lot_purchase_attribute",
        "stock_picking_product_barcode_report",
        "stock_product_shelfinfo",
    ],
    "data": [
        "data/barcode_rule_data.xml",
        "data/paperformat_data.xml",
        "report/report_label_barcode_template.xml",
        "report/report_stock_qr_label.xml",
        "report/report_stock_qr_label_template.xml",
        "report/report_stock_qr_label_zpl.xml",
        "report/report_stock_qr_label_zpl_template.xml",
        "views/product_shelfinfo_views.xml",
        "views/res_config_settings_views.xml",
        "views/stock_location_views.xml",
        "wizard/stock_barcode_selection_printing_views.xml",
    ],
    "installable": True,
}
