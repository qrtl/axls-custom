# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    barcode_report_default_format = fields.Selection(
        selection_add=[("gs1_qr", "Display GS1 QR format for barcodes")],
        ondelete={"gs1_qr": "set null"},
    )
    barcode_label_analytic_plan_id = fields.Many2one(
        "account.analytic.plan",
        string="Analytic plan shown on stock labels",
        help="The stock label prints the analytic account of this plan that the "
        "lot is distributed to. Leave empty to omit that line from the label.",
    )
