# Copyright 2022 Axelspace
# License Other proprietary.

import logging

from numpy import number

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    x_subsidy_summary = fields.Char(
        compute="_compute_x_subsidy_summary", string="Subsidies"
    )

    x_purchase_wf_number = fields.Char(
        string="WF Number",
        help="Purchase WF number for this PO",
    )

    x_purchase_prodorder_number = fields.Char(
        string="Production Order (Seiban)",
        help="Seiban for this PO",
    )

    @api.depends("order_line")
    def _compute_x_subsidy_summary(self):
        # Get all subsidy in purchase lines by list and remove duplicated fields
        for order in self:
            subsidy_list = []
            for line in order.order_line:
                if isinstance(line.x_purchase_subsidy, (number, str)):
                    subsidy_list.append(line.x_purchase_subsidy)
            subsidy_list = set(subsidy_list)
            # _logger.info(",".join(map(str, subsidy_list)))
            order.x_subsidy_summary = ",".join(map(str, sorted(subsidy_list)))
