# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Picking Product Barcode Report GS1 QR",
    "summary": "Print a stock identification label carrying a GS1 QR code",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "category": "Inventory",
    "license": "AGPL-3",
    "maintainers": ["nobuQuartile"],
    "depends": [
        "barcodes_gs1_nomenclature",
        "stock_lot_analytic",
        "stock_lot_purchase_attribute",
        "stock_picking_product_barcode_report",
    ],
    "data": [
        "data/barcode_rule_data.xml",
        "data/paperformat_data.xml",
        "report/report_label_barcode_template.xml",
        "report/report_stock_qr_label.xml",
        "report/report_stock_qr_label_template.xml",
        "views/res_config_settings_views.xml",
        "views/stock_location_views.xml",
        "wizard/stock_barcode_selection_printing_views.xml",
    ],
    "installable": True,
}
