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