# Copyright 2023 Quartile Limited

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
    )
    product_id = fields.Many2one("product.product", "Product")
    solved = fields.Boolean()
    log_id = fields.Many2one("plm.import.log", string="Log", copy=False)
    row_no = fields.Integer("Row No.", copy=False)

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

    def _get_description_purchase(self):
        self.ensure_one()
        return " / ".join([s for s in [self.description, self.drawing, self.spec] if s])

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

    def _create_product(self, mapping):
        self.ensure_one()
        description_purchase = self._get_description_purchase()
        uom = self._get_uom()
        vals = {
            "default_code": self.part_number,
            "name": self.name,
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
        return self.env["product.product"].create(vals)
