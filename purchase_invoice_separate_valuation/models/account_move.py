# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_final_invoice = fields.Boolean(
        string='Final Invoice',
        default=False,
        help='When checked, this invoice will update purchase order quantities and create price difference adjustment entries'
    )
    price_adjustment_move_id = fields.Many2one(
        'account.move',
        string='Price Adjustment Entry',
        readonly=True,
        help='Accounting entry created to adjust the price difference between receipt and final invoice'
    )

    def _post(self, soft=True):
        """
        Override purchase_stock module's _post() to completely bypass 
        price difference application for ALL vendor bills.
        
        This replicates purchase_stock._post() but excludes vendor bills from processing.
        """
        from odoo.tools import float_is_zero
        from odoo.tools.misc import groupby
        
        # Separate vendor bills from other invoices
        vendor_bills = self.filtered(lambda m: m.move_type in ('in_invoice', 'in_refund', 'in_receipt'))
        other_invoices = self - vendor_bills
        
        result = self.env['account.move']
        
        # Process other invoices normally (with purchase_stock logic)
        if other_invoices:
            result |= super(AccountMove, other_invoices)._post(soft)
        
        # Process vendor bills WITHOUT purchase_stock logic
        if vendor_bills:
            # Skip to stock_account and account modules only
            # by importing the base class before purchase_stock
            from odoo.addons.stock_account.models.account_move import AccountMove as StockAccountMove
            result |= StockAccountMove._post(vendor_bills, soft)
            
            # Sync price adjustment entries for vendor bills
            for bill in vendor_bills.filtered(lambda b: b.state == 'posted'):
                bill._sync_price_adjustment_entry()
        
        return result

    def _sync_price_adjustment_entry(self):
        """Create or update a separate accounting entry to adjust GRNI balance for final invoices"""
        self.ensure_one()
        
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info('=== _sync_price_adjustment_entry called for invoice %s ===', self.name)
        _logger.info('is_final_invoice: %s, move_type: %s', self.is_final_invoice, self.move_type)
        
        if not self.is_final_invoice or self.move_type not in ('in_invoice', 'in_refund', 'in_receipt'):
            _logger.info('Skipping: not a final vendor bill')
            if self.price_adjustment_move_id:
                _logger.info('Removing existing adjustment entry because invoice is not final')
                self._remove_price_adjustment_entry()
            return
        
        purchase = self.purchase_id
        if not purchase:
            purchase = self.invoice_line_ids.mapped('purchase_line_id.order_id')[:1]
            if purchase:
                _logger.info('Resolved purchase order from invoice lines: %s', purchase.name)
        if not purchase:
            _logger.warning('Skipping: invoice is not linked to any purchase order')
            return
        
        # Get the configured price adjustment account
        price_adjustment_account = self.company_id.purchase_price_adjustment_account_id
        if not price_adjustment_account:
            _logger.warning('Skipping: price adjustment account not configured in company settings')
            return
        
        _logger.info('Price adjustment account: %s', price_adjustment_account.display_name)

        adjustment_lines = []

        _logger.info('Invoice is linked to purchase order: %s', purchase.name)

        stock_moves = purchase.order_line.mapped('move_ids').filtered(
            lambda m: m.state == 'done' and m.product_id and m.product_id.type == 'product'
            and m.product_id.categ_id.property_valuation == 'real_time'
        )
        _logger.info('Done stock moves: %d', len(stock_moves))

        # Identify GRNI accounts from PO products
        stock_input_account_ids = set()
        for line in purchase.order_line.filtered(lambda l: l.product_id):
            product_accounts = line.product_id.product_tmpl_id._get_product_accounts()
            stock_input_account = product_accounts.get('stock_input')
            if stock_input_account:
                stock_input_account_ids.add(stock_input_account.id)

        # Receipt side (GRNI from stock input) - use accounting entries from stock moves
        receipt_balances = {}
        if stock_moves and stock_input_account_ids:
            receipt_amls = stock_moves.mapped('account_move_ids.line_ids').filtered(
                lambda l: l.account_id.id in stock_input_account_ids and l.move_id.state == 'posted'
            )
        else:
            receipt_amls = self.env['account.move.line']

        for line in receipt_amls:
            receipt_balances.setdefault(line.account_id.id, 0.0)
            receipt_balances[line.account_id.id] += line.balance

        # Invoice side (GRNI from vendor bills) - use GRNI lines from PO-related vendor bills
        po_invoice_moves = purchase.order_line.mapped('invoice_lines').mapped('move_id').filtered(
            lambda m: m.state == 'posted' and m.move_type in ('in_invoice', 'in_refund', 'in_receipt')
        )
        if stock_input_account_ids and po_invoice_moves:
            invoice_lines = self.env['account.move.line'].search([
                ('move_id', 'in', po_invoice_moves.ids),
                ('account_id', 'in', list(stock_input_account_ids)),
            ])
        else:
            invoice_lines = self.env['account.move.line']

        invoice_balances = {}
        for line in invoice_lines:
            invoice_balances.setdefault(line.account_id.id, 0.0)
            invoice_balances[line.account_id.id] += line.balance

        account_ids = set(receipt_balances.keys()) | set(invoice_balances.keys())

        precision_rounding = self.company_id.currency_id.rounding
        for account_id in account_ids:
            receipt_balance = receipt_balances.get(account_id, 0.0)
            invoice_balance = invoice_balances.get(account_id, 0.0)
            total_balance = receipt_balance + invoice_balance

            if float_compare(abs(total_balance), 0.0, precision_rounding=precision_rounding) == 0:
                continue

            stock_input_account = self.env['account.account'].browse(account_id)
            _logger.info(
                'GRNI balance for account %s: receipt=%s, invoice=%s, total=%s',
                stock_input_account.display_name, receipt_balance, invoice_balance, total_balance
            )

            amount = abs(total_balance)
            if total_balance > 0:
                # Debit balance in GRNI -> credit GRNI, debit expense
                adjustment_lines.append({
                    'name': _('GRNI adjustment (Final Invoice %s)') % self.name,
                    'account_id': price_adjustment_account.id,
                    'debit': amount,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                })
                adjustment_lines.append({
                    'name': _('GRNI adjustment (Final Invoice %s)') % self.name,
                    'account_id': stock_input_account.id,
                    'debit': 0.0,
                    'credit': amount,
                    'partner_id': self.partner_id.id,
                })
            else:
                # Credit balance in GRNI -> debit GRNI, credit expense
                adjustment_lines.append({
                    'name': _('GRNI adjustment (Final Invoice %s)') % self.name,
                    'account_id': stock_input_account.id,
                    'debit': amount,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                })
                adjustment_lines.append({
                    'name': _('GRNI adjustment (Final Invoice %s)') % self.name,
                    'account_id': price_adjustment_account.id,
                    'debit': 0.0,
                    'credit': amount,
                    'partner_id': self.partner_id.id,
                })
        
        # Create the adjustment entry if there are lines
        if adjustment_lines:
            if self.price_adjustment_move_id:
                _logger.info('Removing existing adjustment entry before re-creating')
                self._remove_price_adjustment_entry()

            _logger.info('Creating price adjustment entry with %d lines', len(adjustment_lines))
            adjustment_move_vals = {
                'move_type': 'entry',
                'journal_id': self.journal_id.id,
                'date': self.date,
                'ref': _('GRNI Adjustment - Final Invoice %s') % self.name,
                'line_ids': [(0, 0, line) for line in adjustment_lines],
            }
            
            adjustment_move = self.env['account.move'].create(adjustment_move_vals)
            adjustment_move.action_post()
            
            # Link adjustment entry to this invoice
            self.with_context(skip_price_adjustment_sync=True).write({
                'price_adjustment_move_id': adjustment_move.id,
            })
            _logger.info('GRNI adjustment entry created and posted: %s', adjustment_move.name)
        else:
            _logger.info('No adjustment lines created - GRNI already balanced')
            if self.price_adjustment_move_id:
                _logger.info('Removing existing adjustment entry because GRNI is balanced')
                self._remove_price_adjustment_entry()

    def _remove_price_adjustment_entry(self):
        """Remove existing adjustment entry (created by this module)."""
        self.ensure_one()
        adjustment_move = self.price_adjustment_move_id
        if not adjustment_move:
            return
        if adjustment_move.state == 'posted':
            adjustment_move.button_draft()
        adjustment_move.unlink()
        self.with_context(skip_price_adjustment_sync=True).write({
            'price_adjustment_move_id': False,
        })

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_price_adjustment_sync'):
            return res
        if 'is_final_invoice' in vals or 'purchase_id' in vals:
            for move in self.filtered(
                lambda m: m.state == 'posted' and m.move_type in ('in_invoice', 'in_refund', 'in_receipt')
            ):
                move._sync_price_adjustment_entry()
        return res

    @api.model
    def _prepare_invoice_vals_from_purchase(self, purchase_order, final_invoice=False):
        """Prepare invoice values from purchase order with final_invoice flag"""
        vals = purchase_order._prepare_invoice()
        vals['is_final_invoice'] = final_invoice
        return vals


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _create_stock_valuation_layer(self):
        """Override to prevent stock valuation layer creation from vendor bills"""
        if self.move_id.move_type in ('in_invoice', 'in_refund', 'in_receipt'):
            # Skip SVL creation for all vendor bills
            return self.env['stock.valuation.layer']
        return super()._create_stock_valuation_layer()

    def _apply_price_difference(self):
        """
        Block price difference SVL creation for vendor bills.
        This method is triggered by stock_account during posting.
        """
        non_vendor_lines = self.filtered(
            lambda l: l.move_id.move_type not in ('in_invoice', 'in_refund', 'in_receipt')
        )
        if not non_vendor_lines:
            return self.env['stock.valuation.layer'], self.env['account.move.line']
        return super(AccountMoveLine, non_vendor_lines)._apply_price_difference()
