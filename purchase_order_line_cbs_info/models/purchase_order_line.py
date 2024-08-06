# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    cbs_info_ids = fields.One2many("cbs.info", "order_line_id")
    cbs_info_codes = fields.Char(
        string="CBS Info Codes", compute="_compute_cbs_info_codes"
    )

    @api.depends("cbs_info_ids.code")
    def _compute_cbs_info_codes(self):
        for line in self:
            line.cbs_info_codes = ", ".join(line.cbs_info_ids.mapped("code"))

    def action_show_cbs_infos(self):
        self.ensure_one()
        view = self.env.ref(
            "purchase_order_line_cbs_info.view_purchase_order_line_cbs_info_form"
        )
        return {
            "name": _("CBS Infos"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "purchase.order.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
        }
