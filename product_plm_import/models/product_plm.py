# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductPlm(models.Model):
    _name = "product.plm"
    _description = "Product PLM"
    _order = "id desc"

    part_number = fields.Char()
    name = fields.Char()
    esc_code = fields.Char("ESC ID")
    procure_flag = fields.Char("Procure flag")
    item_type = fields.Char()
    category = fields.Char()
    uom = fields.Char("Unit of Material")
    description = fields.Text()
    spec = fields.Char()
    drawing = fields.Char("Drawing No.")
    generic_name = fields.Char()
    company_id = fields.Many2one("res.company", required=True)
    error_message = fields.Text()
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done"), ("failed", "Failed")],
        default="draft",
        string="Status",
    )
    product_id = fields.Many2one("product.product", "Product")
    solved = fields.Boolean()
    log_id = fields.Many2one("plm.import.log", string="Log", copy=False)
    row_no = fields.Integer("Row No.", copy=False)
    mapping_id = fields.Many2one("plm.product.mapping", string="Mapping")

    @api.constrains("solved", "state")
    def _check_solved(self):
        for record in self:
            if record.solved and record.state == "done":
                raise UserError(
                    _("You cannot set a record as solved and done at the same time.")
                )

    def _get_plm_product_mapping(self):
        best_score = -1
        matched_map = self.env["plm.product.mapping"]
        mappings = self.env["plm.product.mapping"].search(
            [("item_type_id.name", "=", self.item_type)]
        )
        for mapping in mappings:
            score_mapping = mapping._get_score(self)
            if score_mapping > best_score:
                matched_map = mapping
                best_score = score_mapping
        return matched_map

    def _get_name(self):
        self.ensure_one()
        return ", ".join([s for s in [self.generic_name, self.name] if s])

    def _get_description_purchase(self):
        self.ensure_one()
        if self.mapping_id.purchase_description_rule == "standard":
            return " / ".join(
                [s for s in [self.generic_name, self.drawing, self.spec] if s]
            )
        return self.description

    def _get_uom(self):
        self.ensure_one()
        uom = False
        if self.uom:
            uom = (
                self.env["uom.uom"]
                .with_context(lang="en_US")
                .search([("name", "=", self.uom)], limit=1)
            )
        if not uom:
            uom = self.env.ref("uom.product_uom_unit")
        return uom

    def _create_product(self):
        self.ensure_one()
        product = self.env["product.product"]
        description_purchase = self._get_description_purchase()
        uom = self._get_uom()
        mapping = self.mapping_id
        vals = {
            "default_code": self.part_number,
            "name": self._get_name(),
            "sale_ok": False,
            "alt_code": self.esc_code,
            "detailed_type": mapping.product_type,
            "categ_id": mapping.product_categ_id.id,
            "uom_id": uom.id,
            "uom_po_id": uom.id,
            "description": self.description,
            "description_purchase": description_purchase,
            "route_ids": [(6, 0, mapping.route_ids.ids)],
            "tracking": mapping.tracking,
            "auto_create_lot": mapping.auto_create_lot,
            "is_via_plm": True,
        }
        try:
            product = self.env["product.product"].create(vals)
        except Exception as e:
            _logger.error(
                "ProductPlm._create_product - failed to create product: %s", str(e)
            )
        return product

    @api.model
    def _get_create_products_domain(self):
        return [("state", "=", "draft"), ("solved", "=", False)]

    @api.model
    def create_products(self, batch_size=30):
        domain = self._get_create_products_domain()
        plm_recs = self.search(domain, limit=batch_size)
        for plm_rec in plm_recs:
            if plm_rec.state != "draft" or plm_rec.error_message or plm_rec.solved:
                continue
            product = plm_rec._create_product()
            if not product:
                plm_rec.write(
                    {
                        "error_message": _("Failed to create product."),
                        "state": "failed",
                    }
                )
                continue
            mapping = plm_rec.mapping_id
            if mapping.lot_sequence_padding:
                product.lot_sequence_id.padding = mapping.lot_sequence_padding
            if mapping.lot_sequence_prefix:
                product.lot_sequence_id.prefix = mapping.lot_sequence_prefix
            product.product_tmpl_id.active = mapping.default_active
            plm_rec.write({"state": "done", "product_id": product.id})
        # This step fails with CasheMiss error in case product creation in
        # _create_product() fails with an exception.
        plm_recs_remain = self.search(domain)
        if plm_recs_remain:
            self.env.ref(
                "product_plm_import.ir_cron_create_products_for_plm_import"
            )._trigger()
