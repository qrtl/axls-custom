# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# "$" also matches before a trailing newline, which would pass a value the
# nomenclature cannot parse back.
CHAR_SET_82 = re.compile(r'\A[!"%-/0-9:-?A-Z_a-z]+\Z')
MAX_LENGTH = {"10": 20, "240": 30}
# "#" is outside character set 82, and unlike the real FNC1 (0x1D) a keyboard
# wedge scanner can transmit it.
FNC1 = "#"


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
    gs1_qr_error = fields.Char("Cannot Be Printed", compute="_compute_gs1_qr")

    @api.depends(
        "product_id",
        "location_id",
        "lot_id.company_id",
        "move_line_id.company_id",
    )
    def _compute_shelfinfo_id(self):
        # A shelf is unique per (product, location, company) and the search sees all.
        shelfinfos = self.env["product.shelfinfo"].search(
            [
                ("product_id", "in", self.product_id.ids),
                ("location_id", "in", self.location_id.ids),
            ]
        )
        by_product_location_company = {
            (
                shelfinfo.product_id.id,
                shelfinfo.location_id.id,
                shelfinfo.company_id.id,
            ): shelfinfo
            for shelfinfo in shelfinfos
        }
        for line in self:
            line.shelfinfo_id = by_product_location_company.get(
                (
                    line.product_id.id,
                    line.location_id.id,
                    line._get_label_company().id,
                )
            )

    @api.depends("lot_id", "move_line_id")
    def _compute_purchase_id(self):
        for line in self:
            line.purchase_id = (
                line.lot_id.purchase_id
                or line.move_line_id.move_id.purchase_line_id.order_id
            )

    @api.depends(
        "lot_id.analytic_distribution",
        "lot_id.company_id",
        "move_line_id.company_id",
    )
    def _compute_analytic_account_id(self):
        for line in self:
            line.analytic_account_id = False
            plan = line._get_label_company().barcode_label_analytic_plan_id
            distribution = line.lot_id.analytic_distribution if plan else None
            if not distribution:
                continue
            line.analytic_account_id = self.env["account.analytic.account"].search(
                [
                    ("id", "in", [int(key) for key in distribution]),
                    ("plan_id", "child_of", plan.id),
                ],
                limit=1,
            )

    @api.depends(
        "product_id",
        "lot_id",
        "lot_id.company_id",
        "move_line_id.company_id",
    )
    def _compute_gs1_qr(self):
        for line in self:
            elements = line._get_gs1_elements()
            line.gs1_qr_error = line._get_gs1_qr_error(elements)
            line.gs1_qr_value = (
                "" if line.gs1_qr_error else line._get_gs1_qr_value(elements)
            )
            line.gs1_qr_hri = "".join("(%s)%s" % element for element in elements)

    def _get_label_company(self):
        # The line has no company of its own: take the stock's, else the active one.
        self.ensure_one()
        return (
            self.lot_id.company_id or self.move_line_id.company_id or self.env.company
        )

    def _get_gs1_elements(self):
        # AI (02) would need a GTIN, and its rule validates a check digit, so a
        # product barcode that merely looks like one makes the whole payload fail
        # to decompose. AI (240) resolves against the internal reference.
        self.ensure_one()
        elements = []
        if self.product_id.default_code:
            elements.append(("240", self.product_id.default_code))
        if self.lot_id:
            elements.append(("10", self.lot_id.name))
        return elements

    def _get_gs1_nomenclature(self):
        # The same resolution stock_barcodes_gs1.process_barcode reads a scan with.
        self.ensure_one()
        return self._get_label_company().nomenclature_id.filtered(
            "is_gs1_nomenclature"
        ) or self.env.ref("barcodes_gs1_nomenclature.default_gs1_nomenclature")

    def _get_separator_error(self):
        # gs1_separator_fnc1 is a configurable regex, not kept in step with FNC1.
        self.ensure_one()
        nomenclature = self._get_gs1_nomenclature()
        # Empty means the reader takes the real FNC1 only.
        separator = nomenclature.gs1_separator_fnc1 or "\x1D"
        if re.fullmatch("(?:%s)" % separator, FNC1):
            return ""
        return _(
            "the barcode nomenclature %(nomenclature)s does not read %(separator)r "
            "back as an FNC1 separator",
            nomenclature=nomenclature.display_name,
            separator=FNC1,
        )

    def _get_gs1_qr_error(self, elements):
        # AI (10) decomposes on its own, so a payload without AI (240) would look
        # scannable and resolve only while that lot name is unique everywhere.
        if not any(ai == "240" for ai, _value in elements):
            return _("the product has no internal reference")
        for ai, value in elements:
            label = _("lot/serial") if ai == "10" else _("internal reference")
            if len(value) > MAX_LENGTH[ai]:
                return _(
                    "the %(label)s %(value)r is longer than the %(length)s "
                    "characters GS1 allows here",
                    label=label,
                    value=value,
                    length=MAX_LENGTH[ai],
                )
            if not CHAR_SET_82.match(value):
                return _(
                    "the %(label)s %(value)r uses characters GS1 cannot encode",
                    label=label,
                    value=value,
                )
        # Only a multi-element payload is closed with a separator.
        if len(elements) > 1:
            return self._get_separator_error()
        return ""

    @api.model
    def _get_gs1_qr_value(self, elements):
        parts = []
        for index, (ai, value) in enumerate(elements):
            parts.append(ai + value)
            # Every element is variable length, so all but the last need closing
            # with FNC1 or the parser reads the next AI as part of the value.
            if index < len(elements) - 1:
                parts.append(FNC1)
        return "".join(parts)

    @api.model
    def _get_label_grid(self):
        # Keep in step with the cell size in the sheet template.
        return 3, 7

    def _get_label_pages(self):
        columns, rows_per_page = self._get_label_grid()
        labels = [line for line in self for _ in range(max(line.label_qty, 0))]
        start = max(self[:1].wizard_id.first_label_position, 1)
        cells = [False] * (start - 1) + labels
        # A fixed-layout table derives its columns from its first row. Pad an
        # incomplete row so that a two-label sheet still has three equal-width
        # columns instead of spreading its two cells over the whole grid.
        cells += [False] * (-len(cells) % columns)
        rows = [
            cells[index : index + columns] for index in range(0, len(cells), columns)
        ]
        return [
            rows[index : index + rows_per_page]
            for index in range(0, len(rows), rows_per_page)
        ]


class WizStockBarcodeSelectionPrinting(models.TransientModel):
    _inherit = "stock.picking.print"

    barcode_format = fields.Selection(
        selection_add=[("gs1_qr", "Display GS1 QR format for barcodes")],
        ondelete={"gs1_qr": "set null"},
    )
    first_label_position = fields.Integer(
        string="Start at Label",
        default=1,
        help="Cell of the first sheet to start printing at, counted left to "
        "right and top to bottom, so 4 is the leftmost cell of the second row. "
        "Use it to fill up a sheet that has already had labels taken off it.",
    )
    is_label_sheet = fields.Boolean(compute="_compute_is_label_sheet")

    @api.depends("barcode_report")
    def _compute_is_label_sheet(self):
        sheet = self.env.ref(
            "stock_picking_product_barcode_report_gs1_qr.action_report_stock_qr_label"
        )
        for wizard in self:
            wizard.is_label_sheet = wizard.barcode_report == sheet

    @api.constrains("first_label_position")
    def _check_first_label_position(self):
        columns, rows = self.env["stock.picking.line.print"]._get_label_grid()
        for wizard in self:
            if not 1 <= wizard.first_label_position <= columns * rows:
                raise ValidationError(
                    _(
                        "The starting label has to be a cell of the sheet, so "
                        "between 1 and %(cells)s, not %(value)s.",
                        cells=columns * rows,
                        value=wizard.first_label_position,
                    )
                )

    @api.onchange("barcode_format")
    def _onchange_barcode_format(self):
        # Which lines belong in the job depends on the format, and the base
        # onchange fires on the report but not on the format.
        self._onchange_picking_ids()

    @api.model
    def _get_move_lines(self, picking):
        # The base keeps only lines whose product has a barcode, which hides the
        # ones a GS1 QR label cannot print. List them all: the wizard says why
        # each faulty one cannot be printed and print_labels refuses.
        if self.barcode_format == "gs1_qr" and self.barcode_report == self.env.ref(
            "stock_picking_product_barcode_report.action_label_barcode_report"
        ):
            return (
                self.env["stock.move.line"].browse(
                    self.env.context.get("stock_move_line_to_print", [])
                )
                or picking.move_line_ids
            )
        return super()._get_move_lines(picking)

    def print_labels(self):
        faulty = self._get_gs1_qr_lines().filtered("gs1_qr_error")
        if faulty:
            raise UserError(
                _("These labels would carry no scannable code:\n\n%s")
                % "\n".join(
                    "- %s%s: %s"
                    % (
                        line.product_id.display_name,
                        " / %s" % line.lot_id.name if line.lot_id else "",
                        line.gs1_qr_error,
                    )
                    for line in faulty
                )
            )
        return super().print_labels()

    def _get_gs1_qr_lines(self):
        if self.is_custom_label:
            return self.env["stock.picking.line.print"]
        # The sheet report always prints the symbol, and the format is a
        # statement about the job rather than about one report, so while either
        # applies the check holds for every report the wizard can reach.
        if self.barcode_format == "gs1_qr" or self.barcode_report == self.env.ref(
            "stock_picking_product_barcode_report_gs1_qr.action_report_stock_qr_label"
        ):
            return self.product_print_moves.filtered(lambda line: line.label_qty > 0)
        return self.env["stock.picking.line.print"]

    @api.model
    def _prepare_data_from_move_line(self, move_line):
        values = super()._prepare_data_from_move_line(move_line)
        # At receipt the stock is not on its shelf yet, so the destination is the
        # best "where is it now". Going out, the destination is the customer and
        # only the source is a place a shelf can be keyed on.
        location = move_line.location_dest_id
        if location.usage != "internal":
            location = move_line.location_id
        values["location_id"] = location.id
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
        # super() builds exactly one command per lot, in browse order. A lot
        # split across shelves gets the first of them.
        for line, lot in zip(lines, lots):
            quants = lot.quant_ids.filtered(
                lambda quant: quant.location_id.usage == "internal" and quant.quantity
            )
            line[2]["location_id"] = quants[:1].location_id.id
        return lines
