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
    revision = fields.Char(string="Revision", help="Product revision number")
    company_id = fields.Many2one("res.company", required=True)
    error_message = fields.Text()
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done"), ("failed", "Failed")],
        default="draft",
        string="Status",
    )
    product_id = fields.Many2one("product.product", "Product")
    existing_product_id = fields.Many2one("product.product", "Existing Product", help="Used for updating existing products")
    solved = fields.Boolean()
    log_id = fields.Many2one("plm.import.log", string="Log", copy=False)
    row_no = fields.Integer("Row No.", copy=False)
    acceptance_test_categ = fields.Char(string="Quality Check Category")
    quality_check_categ_id = fields.Many2one(
        "quality.check.category", string="Quality Check Category"
    )
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
            "quality_check_categ_id": self.quality_check_categ_id.id,
            "uom_po_id": uom.id,
            "description": self.description,
            "description_purchase": description_purchase,
            "route_ids": [(6, 0, mapping.route_ids.ids)],
            "tracking": mapping.tracking,
            "auto_create_lot": mapping.auto_create_lot,
            "is_via_plm": True,
            "active": mapping.default_active,  # Active status determined by mapping configuration
        }
        try:
            product = self.env["product.product"].create(vals)
            
            # Ensure important fields are set on product.template as well
            if product and product.product_tmpl_id:
                # First, explicitly set the active status on the template with sudo
                self.env['product.template'].sudo().browse(product.product_tmpl_id.id).write({
                    'active': mapping.default_active,
                })
                
                # Then update other fields
                product.product_tmpl_id.write({
                    "default_code": self.part_number,
                    "alt_code": self.esc_code,
                    "description": self.description,
                    "description_purchase": description_purchase,
                    "is_via_plm": True,
                })
                
                # Log the active status for debugging
                _logger.info(
                    "Product template active status: %s (mapping.default_active: %s)",
                    product.product_tmpl_id.active,
                    mapping.default_active,
                )
                
        except Exception as e:
            _logger.error(
                "ProductPlm._create_product - failed to create product: %s", str(e)
            )
        return product
    
    def _create_product_revision(self, product):
        """Create a revision for the product if revision number is provided"""
        self.ensure_one()
        if not self.revision or not product:
            return False
            
        # Create revision for product.template
        template_revision_vals = {
            "product_tmpl_id": product.product_tmpl_id.id,
            "revision_number": self.revision,
            "name": f"{product.name} Rev. {self.revision}",
            "internal_product_id": product.default_code,
        }
        
        try:
            self.env["product.revision"].create(template_revision_vals)
            _logger.info(
                "Created revision %s for product template %s",
                self.revision,
                product.product_tmpl_id.id,
            )
        except Exception as e:
            _logger.error(
                "Failed to create revision for product template: %s", str(e)
            )
            
        # If this is not the default variant, create a variant-specific revision
        # Check if this is the default variant (only variant for the template)
        if len(product.product_tmpl_id.product_variant_ids) > 1:
            variant_revision_vals = {
                "product_id": product.id,
                "revision_number": self.revision,
                "name": f"{product.name} Rev. {self.revision}",
                "internal_product_id": product.default_code,
            }
            
            try:
                self.env["product.revision"].create(variant_revision_vals)
                _logger.info(
                    "Created revision %s for product variant %s",
                    self.revision,
                    product.id,
                )
            except Exception as e:
                _logger.error(
                    "Failed to create revision for product variant: %s", str(e)
                )
                
        return True

    def _log_product_update(self, product, old_values, new_revision=None, old_revision=None, is_new=False):
        """Record a log note for product updates or creation"""
        self.ensure_one()
        
        # Get the import file name from the log
        eco_file_name = self.log_id.file_name if self.log_id else "Unknown"
        
        # Prepare the log message
        if is_new:
            log_message = f"<p><strong>Product created from PLM import</strong></p>"
        else:
            log_message = f"<p><strong>Product updated from PLM import</strong></p>"
        log_message += f"<p><strong>ECO File:</strong> {eco_file_name}</p>"
        
        # Add changed fields information
        if old_values:
            log_message += "<p><strong>Updated fields:</strong></p><ul>"
            for field, old_value in old_values.items():
                field_label = product._fields[field].string if field in product._fields else field
                
                # Handle special case for quality_check_categ_id
                if field == "quality_check_categ_id":
                    new_value = product.quality_check_categ_id.name if product.quality_check_categ_id else ""
                else:
                    new_value = getattr(product, field, "")
                    
                if old_value != new_value:
                    log_message += f"<li>{field_label}: {old_value} → {new_value}</li>"
            log_message += "</ul>"
        
        # Add revision change information
        if new_revision and old_revision:
            log_message += f"<p><strong>Revision changed:</strong> {old_revision} → {new_revision}</p>"
        elif new_revision:
            log_message += f"<p><strong>New revision added:</strong> {new_revision}</p>"
        
        # Post the log note to product.product
        product.message_post(body=log_message, subtype_xmlid="mail.mt_note")
        
        # Post the log note to product.template if it's different from product.product
        if product.product_tmpl_id:
            product.product_tmpl_id.message_post(body=log_message, subtype_xmlid="mail.mt_note")
    
    def _update_product(self, product):
        """Update an existing product with new information"""
        self.ensure_one()
        if not product:
            return False
            
        # Store old values for logging
        old_values = {
            "name": product.name,
            "alt_code": product.alt_code,
            "description": product.description,
            "description_purchase": product.description_purchase,
            "quality_check_categ_id": product.quality_check_categ_id.name if product.quality_check_categ_id else "",
        }
        
        # Get current revision for logging
        old_revision = None
        current_revision = self.env["product.revision"].search([
            "|",
            ("product_id", "=", product.id),
            ("product_tmpl_id", "=", product.product_tmpl_id.id),
            ("active", "=", True),
        ], limit=1)
        if current_revision:
            old_revision = current_revision.revision_number
            
        description_purchase = self._get_description_purchase()
        uom = self._get_uom()
        mapping = self.mapping_id
        
        # Update product.product
        try:
            product.write({
                "name": self._get_name(),
                "alt_code": self.esc_code,
                "quality_check_categ_id": self.quality_check_categ_id.id,
                "description": self.description,
                "description_purchase": description_purchase,
                "route_ids": [(6, 0, mapping.route_ids.ids)],
                "tracking": mapping.tracking,
                "auto_create_lot": mapping.auto_create_lot,
            })
            
            # Update product.template fields
            product.product_tmpl_id.write({
                "name": self._get_name(),
                "alt_code": self.esc_code,
                "description": self.description,
                "description_purchase": description_purchase,
            })
            
            # Update lot sequence if needed
            if mapping.lot_sequence_padding:
                product.lot_sequence_id.padding = mapping.lot_sequence_padding
            if mapping.lot_sequence_prefix:
                product.lot_sequence_id.prefix = mapping.lot_sequence_prefix
            
            # Log the product update
            self._log_product_update(product, old_values, self.revision, old_revision)
                
            _logger.info(
                "Updated product %s (%s)",
                product.id,
                self.part_number,
            )
            return product
        except Exception as e:
            _logger.error(
                "ProductPlm._update_product - failed to update product: %s", str(e)
            )
            return False
    
    def _should_create_new_revision(self, product):
        """Check if a new revision should be created based on revision numbers"""
        self.ensure_one()
        if not self.revision or not product:
            return False
            
        # Get the current revision for the product
        current_revision = False
        if len(product.product_tmpl_id.product_variant_ids) > 1:
            # For multi-variant products, check variant-specific revision
            current_revision = self.env["product.revision"].search([
                ("product_id", "=", product.id),
                ("active", "=", True),
            ], limit=1)
        
        if not current_revision:
            # Check template revision
            current_revision = self.env["product.revision"].search([
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ("active", "=", True),
            ], limit=1)
            
        if not current_revision:
            # No current revision, so create a new one
            return True
            
        # Compare revision numbers
        try:
            # Try numeric comparison first
            current_rev_num = int(current_revision.revision_number)
            new_rev_num = int(self.revision)
            return new_rev_num > current_rev_num
        except (ValueError, TypeError):
            # If not numeric, do string comparison
            return self.revision > current_revision.revision_number
    
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
                
            # Check if this is an update to an existing product
            if plm_rec.existing_product_id:
                product = plm_rec.existing_product_id
                product = plm_rec._update_product(product)
                if not product:
                    plm_rec.write({
                        "error_message": _("Failed to update product."),
                        "state": "failed",
                    })
                    continue
                    
                # Check if we need to create a new revision
                if plm_rec.revision and plm_rec._should_create_new_revision(product):
                    plm_rec._create_product_revision(product)
                    
                plm_rec.write({"state": "done", "product_id": product.id})
                continue
                
            # Create new product
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
            # The active status is already set during product creation based on mapping.default_active
            
            # Create product revision if revision number is provided
            if plm_rec.revision:
                plm_rec._create_product_revision(product)
            
            # Log the product creation
            plm_rec._log_product_update(
                product, 
                {}, 
                new_revision=plm_rec.revision,
                old_revision=None,
                is_new=True
            )
                
            plm_rec.write({"state": "done", "product_id": product.id})
        # This step fails with CasheMiss error in case product creation in
        # _create_product() fails with an exception.
        plm_recs_remain = self.search(domain)
        if plm_recs_remain:
            self.env.ref(
                "product_plm_import.ir_cron_create_products_for_plm_import"
            )._trigger()
