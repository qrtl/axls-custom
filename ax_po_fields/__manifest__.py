# Copyright 2022 Axelspace
# License Other proprietary.

{
    "name": "Ax PO Fields",
    "summary": """
        Additional fields for Axelspace""",
    "version": "16.0.0.0.0",
    "license": "Other proprietary",
    "author": "Axelspace, Quartile Limited",
    "depends": ["base", "purchase"],
    "data": [
        "security/purchase_order_line.xml",
        "security/purchase_order.xml",
        "views/purchase_order.xml",
    ],
    "external_dependencies": {
        "bin": [],
        "python": [
            "numpy",
        ],
    },
    "installable": True,
    "demo": [],
}
