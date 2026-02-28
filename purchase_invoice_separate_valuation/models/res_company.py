# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    purchase_price_adjustment_account_id = fields.Many2one(
        'account.account',
        string='Purchase Price Adjustment Account',
        help='Account used for price difference adjustments when posting final vendor bills',
        domain="[('deprecated', '=', False), ('company_id', '=', id)]",
    )
    purchase_grni_adjustment_journal_id = fields.Many2one(
        'account.journal',
        string='GRNI Adjustment Journal',
        help='Journal used for GRNI balancing entries created when a final vendor bill is posted. '
             'Should be a general/miscellaneous journal, not the accounts payable journal. '
             'Falls back to the first available general journal if not set.',
        domain="[('type', '=', 'general'), ('company_id', '=', id)]",
    )
