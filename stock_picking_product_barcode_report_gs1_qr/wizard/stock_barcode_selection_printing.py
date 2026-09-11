# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import re

from odoo import api, fields, models

# GS1 "encodable character set 82", spelled exactly as Odoo's own AI (10) rule
# pattern spells it so that what we print is what the nomenclature parses back.
GS1_CHAR_SET_82 = re.compile(r'^[!"%-/0-9:-?A-Z_a-z]+$')
# Maximum value length per application identifier, per the GS1 general
# specification. AI (02) is fixed length, the other two are variable.
GS1_MAX_LENGTH = {"02": 14, "10": 20, "240": 30}
VARIABLE_LENGTH_AI = ("10", "240")
# A keyboard wedge scanner cannot type the real FNC1 (0x1D) into a web form, so
# the payload separates elements with "#", which barcode.nomenclature accepts
# out of the box through the default gs1_separator_fnc1 regex. "#" is outside
# character set 82, so it can never occur inside an element value.
FNC1 = "#"
# Grid of the A4 label sheet. Keep in step with the margins of
# paperformat_stock_qr_label_a4: 4 * 47mm across and 10 * 29mm down.
LABEL_COLUMNS = 4
LABEL_ROWS = 10


class ProductPrintingQty(models.TransientModel):
    _inherit = "stock.picking.line.print"

    location_id = fields.Many2one("stock.location", string="Location")
    shelfinfo_id = fields.Many2one(
        "product.shelfinfo", string="Shelf Info.", compute="_compute_shelfinfo_id"
    )
    purchase_id = fields.Many2one(
        "purchase.order", string="Purchase Order", compute="_compute_purchase_id"
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        compute="_compute_analytic_account_id",
    )
    gs1_qr_value = fields.Char("GS1 QR Value", compute="_compute_gs1_qr")
    gs1_qr_hri = fields.Char(
        "GS1 Human Readable Interpretation", compute="_compute_gs1_qr"
    )

    @api.depends("product_id", "location_id")
    def _compute_shelfinfo_id(self):
        # The shelf is not the stock location: locations here are warehouse-wide
        # (one per company), and the shelf address lives on product.shelfinfo,
        # keyed by exactly this pair. Resolved the same way stock.quant does.
        shelfinfos = self.env["product.shelfinfo"].search(
            [
                ("product_id", "in", self.product_id.ids),
                ("location_id", "in", self.location_id.ids),
            ]
        )
        by_product_location = {
            (shelfinfo.product_id.id, shelfinfo.location_id.id): shelfinfo
            for shelfinfo in shelfinfos
        }
        for line in self:
            line.shelfinfo_id = by_product_location.get(
                (line.product_id.id, line.location_id.id)
            )

    @api.depends("lot_id", "move_line_id")
    def _compute_purchase_id(self):
        for line in self:
            # stock_lot_purchase_attribute stamps the lot at receipt, which is the
            # only source available when printing from a quant or a lot. Fall back
            # to the move line so a receipt prints even before that is stamped.
            line.purchase_id = (
                line.lot_id.purchase_id
                or line.move_line_id.move_id.purchase_line_id.order_id
            )

    @api.depends("lot_id")
    def _compute_analytic_account_id(self):
        plan = self.env.company.barcode_label_analytic_plan_id
        for line in self:
            distribution = line.lot_id.analytic_distribution if plan else None
            accounts = (
                self.env["account.analytic.account"]
                .browse(int(key) for key in distribution or {})
                .exists()
            )
            line.analytic_account_id = accounts.filtered(
                lambda account: plan in (account.plan_id | account.root_plan_id)
            )[:1]

    @api.depends("product_id", "lot_id")
    def _compute_gs1_qr(self):
        for line in self:
            elements = line._get_gs1_elements()
            line.gs1_qr_value = line._get_gs1_qr_value(elements)
            line.gs1_qr_hri = "".join("(%s)%s" % element for element in elements)

    def _get_gs1_elements(self):
        """Return the (AI, value) pairs identifying this line's stock."""
        self.ensure_one()
        product = self.product_id
        elements = []
        if product.barcode and product.barcode.isdigit() and len(product.barcode) <= 14:
            elements.append(("02", product.barcode.zfill(14)))
        elif product.default_code:
            # Without a GTIN there is nothing to put in AI (02). AI (240) carries
            # the manufacturer's own identification instead, which
            # stock_barcodes_gs1 resolves against the internal reference.
            elements.append(("240", product.default_code))
        if self.lot_id:
            elements.append(("10", self.lot_id.name))
        return elements

    @api.model
    def _get_gs1_qr_value(self, elements):
        """Encode the elements as a GS1 payload, or "" if any cannot be encoded."""
        if not elements or not all(
            len(value) <= GS1_MAX_LENGTH[ai] and GS1_CHAR_SET_82.match(value)
            for ai, value in elements
        ):
            return ""
        parts = []
        for index, (ai, value) in enumerate(elements):
            parts.append(ai + value)
            # A variable length element that is not the last one has to be closed
            # with FNC1, or the parser reads the following AI as part of its value.
            if ai in VARIABLE_LENGTH_AI and index < len(elements) - 1:
                parts.append(FNC1)
        return "".join(parts)

    def _get_label_pages(self):
        """Lay the labels of these lines out as sheets of rows of cells."""
        labels = [line for line in self for _ in range(max(line.label_qty, 0))]
        rows = [
            labels[index : index + LABEL_COLUMNS]
            for index in range(0, len(labels), LABEL_COLUMNS)
        ]
        return [
            rows[index : index + LABEL_ROWS]
            for index in range(0, len(rows), LABEL_ROWS)
        ]


class WizStockBarcodeSelectionPrinting(models.TransientModel):
    _inherit = "stock.picking.print"

    barcode_format = fields.Selection(
        selection_add=[("gs1_qr", "Display GS1 QR format for barcodes")],
        ondelete={"gs1_qr": "set null"},
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        ctx = self.env.context
        if ctx.get("active_ids") and ctx.get("active_model") == "stock.location":
            res.update({"product_print_moves": self._get_lines_from_locations()})
        if ctx.get("active_ids") and ctx.get("active_model") == "product.shelfinfo":
            res.update({"product_print_moves": self._get_lines_from_shelfinfos()})
        return res

    @api.model
    def _get_move_lines(self, picking):
        # AI (240) identifies the product by its internal reference, so a product
        # that has no barcode at all still prints. The base module drops those
        # lines because the plain and GS1-128 formats have nothing to encode.
        if self.barcode_format == "gs1_qr" and self.barcode_report == self.env.ref(
            "stock_picking_product_barcode_report.action_label_barcode_report"
        ):
            return self.env["stock.move.line"].browse(
                self.env.context.get("stock_move_line_to_print", [])
            ) or picking.move_line_ids.filtered("product_id.default_code")
        return super()._get_move_lines(picking)

    @api.model
    def _prepare_data_from_move_line(self, move_line):
        values = super()._prepare_data_from_move_line(move_line)
        # At receipt the stock is not on its shelf yet, so the destination of the
        # move is the best "where is it now" the label can carry.
        values["location_id"] = move_line.location_dest_id.id
        return values

    def _get_lines_from_quants(self):
        lines = super()._get_lines_from_quants()
        quants = self.env["stock.quant"].browse(self.env.context["active_ids"])
        # super() builds exactly one command per quant, in browse order.
        for line, quant in zip(lines, quants):
            line[2]["location_id"] = quant.location_id.id
        return lines

    def _get_lines_from_lots(self):
        lines = super()._get_lines_from_lots()
        lots = self.env["stock.lot"].browse(self.env.context["active_ids"])
        # super() builds exactly one command per lot, in browse order. A lot split
        # across shelves gets the first of them; printing per quant instead of per
        # lot is the way to label each shelf.
        for line, lot in zip(lines, lots):
            quants = lot.quant_ids.filtered(
                lambda quant: quant.location_id.usage == "internal" and quant.quantity
            )
            line[2]["location_id"] = quants[:1].location_id.id
        return lines

    def _get_lines_from_shelfinfos(self):
        """One label line per quant sitting on the selected shelves."""
        shelfinfos = self.env["product.shelfinfo"].browse(
            self.env.context["active_ids"]
        )
        quants = self.env["stock.quant"].search(
            [("shelfinfo_id", "in", shelfinfos.ids), ("quantity", ">", 0)]
        )
        return self.with_context(active_ids=quants.ids)._get_lines_from_quants()

    def _get_lines_from_locations(self):
        """One label line per quant stored anywhere under the selected locations."""
        locations = self.env["stock.location"].browse(self.env.context["active_ids"])
        quants = self.env["stock.quant"].search(
            [
                ("location_id", "child_of", locations.ids),
                ("location_id.usage", "=", "internal"),
                ("quantity", ">", 0),
            ]
        )
        return self.with_context(active_ids=quants.ids)._get_lines_from_quants()
