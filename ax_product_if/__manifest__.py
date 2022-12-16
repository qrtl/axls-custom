# Copyright 2022 Axelspace
# License Other proprietary.

{
    "name": "Ax Product If",
    "summary": """
        Product import""",
    "version": "16.0.0.0.0",
    "license": "Other proprietary",
    "author": "Axelspace, Quartile Limited",
    "depends": [
        "base",
        "purchase",
    ],
    "data": [
        "data/cron.xml",
        "wizards/res_products_if_update_wizard.xml",
        "security/ir.model.access.csv",
        "security/res_products_if_provider.xml",
        "views/res_products_if_provider.xml",
        "views/res_config_settings.xml",
    ],
    "external_dependencies": {
        "bin": [],
        "python": [
            "pandas",
        ],
    },
    "installable": True,
    "demo": [],
}
