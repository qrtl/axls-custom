# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    line_analytic_account_ids = fields.Many2many(
        "account.analytic.account",
        string="Analytic Accounts of Lines",
        compute="_compute_line_analytic_account_ids",
        store=True,
        help="Analytic accounts the lines of the order are distributed to. It "
        "holds the accounts of every line, so the order still shows what it is "
        "distributed to when its lines differ, and it is stored, so the orders "
        "can be filtered by analytic account.",
    )

    @api.depends("order_line.analytic_distribution")
    def _compute_line_analytic_account_ids(self):
        # The keys of the analytic_distribution json field are the ids of the
        # analytic accounts the distribution applies to.
        account_ids_by_order = {
            order: {
                int(account_id)
                for line in order.order_line
                for account_id in line.analytic_distribution or {}
            }
            for order in self
        }
        # The json field holds no database reference and may still refer to a
        # deleted account, which the order cannot be linked to. exists rather
        # than search, as an archived account is one the order is distributed
        # to just as much, and dropping it would not bring it back when the
        # account is unarchived.
        accounts = self.env["account.analytic.account"].browse(
            sorted(set().union(*account_ids_by_order.values()))
        )
        existing_ids = set(accounts.exists().ids)
        for order, account_ids in account_ids_by_order.items():
            order.line_analytic_account_ids = accounts.browse(
                sorted(account_ids & existing_ids)
            )
