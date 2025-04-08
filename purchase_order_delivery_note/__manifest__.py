# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Purhcase Order Delivery Note",
    "category": "Purchase",
    "version": "16.0.1.0.0",
    "author": "Quartile",
    "website": "https://www.quartile.co",
    "license": "AGPL-3",
    "depends": ["purchase_stock", "stock_picking_line_sequence"],
    "data": [
        "reports/purchase_order_delivery_note.xml",
        "reports/purchase_order_delivery_templates.xml",
    ],
    "installable": True,
}
