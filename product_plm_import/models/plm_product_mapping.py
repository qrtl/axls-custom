# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import fnmatch

from odoo import api, fields, models


class PlmProductMapping(models.Model):
    _name = "plm.product.mapping"
    _description = "PLM-Product Mapping"
    _order = "item_type_id"
    _rec_name = "item_type_id"

    item_type_id = fields.Many2one("plm.item.type", string="Item Type", required=True)
    category_ids = fields.Many2many("plm.category", string="Categories")
    procure_flag_ids = fields.Many2many("plm.procure.flag", string="Procure Flags")
    product_type = fields.Selection(
        selection=lambda self: self.env["product.template"]
        ._fields["detailed_type"]
        .selection,
        required=True,
    )
    purchase_description_rule = fields.Selection(
        selection=[
            ("standard", "Standard: [Generic Name] / [Drawing] / [Spec]"),
            ("generic_name", "Generic Name"),
        ],
        default="standard",
    )
    product_categ_id = fields.Many2one(
        "product.category",
        string="Product Category",
        required=True,
    )
    route_ids = fields.Many2many("stock.route", string="Routes")
    tracking = fields.Selection(
        selection=lambda self: self.env["product.template"]
        ._fields["tracking"]
        .selection,
        default="none",
        required=True,
    )
    auto_create_lot = fields.Boolean()
    lot_sequence_padding = fields.Integer()
    lot_sequence_prefix = fields.Char()
    default_active = fields.Boolean(
        help="Default value for active field of the created product."
    )
    company_id = fields.Many2one("res.company")
    active = fields.Boolean(default=True)

    @api.onchange("product_type")
    def onchange_product_type(self):
        if self.product_type != "product":
            self.tracking = "none"
            self.auto_create_lot = False
            self.lot_sequence_padding = False
            self.lot_sequence_prefix = False

    @api.onchange("tracking")
    def onchange_tracking(self):
        if self.tracking == "none":
            self.auto_create_lot = False

    @api.onchange("auto_create_lot")
    def onchange_auto_create_lot(self):
        if not self.auto_create_lot:
            self.lot_sequence_padding = False
            self.lot_sequence_prefix = False

    def _get_score(self, plm):
        """Gives the score of the mapping record with field values of self."""
        self.ensure_one()
        score = 0.0
        if plm.category:
            category_names = self.category_ids.mapped("name")
            if category_names:
                if plm.category in category_names:
                    score += 1.0
                # Wildcard matching with `*`/`?`
                elif any(
                    fnmatch.fnmatch(plm.category, pattern) for pattern in category_names
                ):
                    score += 0.5
                else:
                    score -= 1.0
        if plm.procure_flag:
            procure_flag_names = self.procure_flag_ids.mapped("name")
            if plm.procure_flag in procure_flag_names:
                score += 1
            elif procure_flag_names and plm.procure_flag not in procure_flag_names:
                score -= 1
        return score
