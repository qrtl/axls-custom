# Copyright 2022 Axelspace
# License Other proprietary.
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AxProdProcurabilityUpdateWizard(models.TransientModel):
    _name = "ax_prod_procurability.update.wizard"
    _description = "Procurability Update Wizard"

    process_flg = fields.Selection(
        [
            ("addupd", "Add new item and update"),
            ("updonly", "Update only"),
            ("addonly", "Add new item only"),
        ],
        default="addupd",
        string="Processing Type",
    )

    def action_update(self):
        self.ensure_one()
        if self.process_flg == "addonly":
            self.env["ax_prod_procurability"].add_new_products()
        elif self.process_flg == "updonly":
            self.env["ax_prod_procurability"].update_procurability_info()
        else:
            self.env["ax_prod_procurability"].add_new_products()
            self.env["ax_prod_procurability"].update_procurability_info()

        # ax_prod_procurability_act_window を開き直したい
        # return {"type": "ir.actions.act_window_close"}
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
