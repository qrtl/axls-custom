# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_price_adjustment_account_id = fields.Many2one(
        'account.account',
        related='company_id.purchase_price_adjustment_account_id',
        string='Purchase Price Adjustment Account',
        readonly=False,
        help='Default expense account used for price difference adjustments when posting final vendor bills. '
             'This account will be used instead of the product expense account.',
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
    )
    purchase_grni_adjustment_journal_id = fields.Many2one(
        'account.journal',
        related='company_id.purchase_grni_adjustment_journal_id',
        string='GRNI Adjustment Journal',
        readonly=False,
        help='Journal used for GRNI balancing entries created when a final vendor bill is posted. '
             'Should be a general/miscellaneous journal. Falls back to the first general journal if not set.',
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    )