# Copyright 2025 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sep_val_move_type = fields.Selection(
        [
            ("advance_bill", "Advance Bill"),
            ("final_bill", "Final Bill"),
            ("advance_application", "Application Credit Note"),
            ("adjustment_entry", "Adjustment Entry"),
        ],
        string="Sep. Val. Type",
        copy=False,
        help="Separate valuation document type.",
    )
    sep_val_purchase_id = fields.Many2one(
        "purchase.order",
        string="Sep. Val. Purchase Order",
        copy=False,
        ondelete="set null",
        help="Purchase order this document is linked to (Separate Valuation Mode).",
    )
    sep_val_origin_move_id = fields.Many2one(
        "account.move",
        string="Origin Advance Bill",
        copy=False,
        ondelete="set null",
        help="Advance bill this application credit note is derived from.",
    )
    sep_val_target_move_id = fields.Many2one(
        "account.move",
        string="Target Final Bill",
        copy=False,
        ondelete="set null",
        help="Final bill this application credit note was reconciled against.",
    )
    sep_val_application_move_ids = fields.One2many(
        "account.move",
        "sep_val_origin_move_id",
        string="Application Credit Notes",
        help="Application credit notes derived from this advance bill.",
    )
    sep_val_advance_applied_amount = fields.Monetary(
        string="Applied Amount",
        compute="_compute_sep_val_advance_amounts",
        currency_field="currency_id",
        help="Sum of posted application credit note untaxed amounts.",
    )
    sep_val_advance_remaining_amount = fields.Monetary(
        string="Remaining Amount",
        compute="_compute_sep_val_advance_amounts",
        currency_field="currency_id",
        help="Untaxed amount of this advance bill minus the applied amount.",
    )

    @api.depends(
        "sep_val_move_type",
        "amount_untaxed",
        "sep_val_application_move_ids.state",
        "sep_val_application_move_ids.amount_untaxed",
    )
    def _compute_sep_val_advance_amounts(self):
        for move in self:
            if move.sep_val_move_type != "advance_bill":
                move.sep_val_advance_applied_amount = 0.0
                move.sep_val_advance_remaining_amount = 0.0
                continue
            applied = sum(
                cn.amount_untaxed
                for cn in move.sep_val_application_move_ids
                if cn.state == "posted"
            )
            move.sep_val_advance_applied_amount = applied
            move.sep_val_advance_remaining_amount = move.amount_untaxed - applied

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            order = move.sep_val_purchase_id
            if not order:
                continue
            if move.sep_val_move_type == "advance_bill":
                order._create_paired_credit_note(move)
            elif move.sep_val_move_type == "final_bill":
                order._settle_final_bill(move)
        return posted
