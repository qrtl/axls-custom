# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Picking Validate Jobcan WF",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Stock",
    "license": "AGPL-3",
    "depends": ["stock", "base_api_connection"],
    "data": [
        "data/api_config_data.xml",
        "data/cron_data.xml",
        "data/mail_message_subtype_data.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
