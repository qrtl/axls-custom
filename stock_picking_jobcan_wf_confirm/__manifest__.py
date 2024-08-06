# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Picking Jobcan WF Confirmation",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Stock",
    "license": "AGPL-3",
    "depends": ["stock", "stock_picking_validate_jobcan_wf"],
    "data": [
        "security/ir.model.access.csv",
        "data/cron_data.xml",
    ],
    "installable": True,
    "application": False,
}
