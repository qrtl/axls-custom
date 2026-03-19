# -*- coding: utf-8 -*-
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_separate_valuation_purchase_orders(self):
        return (
            self.mapped('purchase_line_id.order_id')
            | self.mapped('origin_returned_move_id.purchase_line_id.order_id')
        ).filtered(lambda po: po.use_separate_valuation and po._get_final_invoice())

    def _action_done(self, cancel_backorder=False):
        result = super()._action_done(cancel_backorder=cancel_backorder)
        self._get_separate_valuation_purchase_orders()._sync_price_adjustment_entry()
        return result

    def _action_cancel(self):
        purchases = self._get_separate_valuation_purchase_orders()
        result = super()._action_cancel()
        purchases._sync_price_adjustment_entry()
        return result
