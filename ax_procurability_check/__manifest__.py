# Copyright 2022 Axelspace
# License Other proprietary.

{
    "name": "Ax Procurability Check",
    "summary": """
        Check part procurability and save status of investigation""",
    "version": "16.0.0.0.0",
    "license": "Other proprietary",
    "author": "Axelspace, Quartile Limited",
    "depends": ["base", "mail", "stock", "purchase"],
    "data": [
        "data/cron.xml",
        "views/product_template.xml",
        "security/ax_prod_procurability.xml",
        "security/res_company.xml",
        "security/res_config_settings.xml",
        "views/ax_prod_procurability.xml",
        "views/res_config_settings.xml",
        "wizards/ax_prod_procurability_update_wizard.xml",
    ],
    "demo": [
        "demo/ax_prod_procurability.xml",
    ],
}
