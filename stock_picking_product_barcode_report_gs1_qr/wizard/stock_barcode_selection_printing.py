# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


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

    @api.depends("product_id", "location_id")
    def _compute_shelfinfo_id(self):
        # The shelf is not the stock location: locations here are warehouse-wide,
        # and the shelf address lives on product.shelfinfo, keyed by this pair.
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
            # The lot is stamped at receipt, which is the only source available
            # when printing from a quant or a lot. Fall back to the move line so
            # that a receipt prints before the stamp is there.
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
            # The plan is configured on the company whose stock is being
            # labelled, which is not necessarily the active one: the wizard is
            # reachable from quants and lots across every allowed company.
            company = (
                line.lot_id.company_id
                or line.move_line_id.company_id
                or self.env.company
            )
            plan = company.barcode_label_analytic_plan_id
            distribution = line.lot_id.analytic_distribution if plan else None
            if not distribution:
                continue
            # child_of so that a plan configured as the root also matches the
            # accounts of its sub-plans. search() rather than browse().filtered()
            # so that the record rules drop what the user may not see instead of
            # raising out of a compute.
            line.analytic_account_id = self.env["account.analytic.account"].search(
                [
                    ("id", "in", [int(key) for key in distribution]),
                    ("plan_id", "child_of", plan.id),
                ],
                limit=1,
            )

    @api.depends("product_id", "lot_id")
    def _compute_gs1_qr(self):
        for line in self:
            elements = line._get_gs1_elements()
            line.gs1_qr_error = line._get_gs1_qr_error(elements)
            line.gs1_qr_value = (
                "" if line.gs1_qr_error else line._get_gs1_qr_value(elements)
            )
            line.gs1_qr_hri = "".join("(%s)%s" % element for element in elements)

    def _get_gs1_elements(self):
        """Return the (AI, value) pairs identifying this line's stock.

        The product is always AI (240), the manufacturer's own identification,
        which stock_barcodes_gs1 resolves against the internal reference. AI (02)
        would need a GTIN, and a product barcode that merely looks like one is
        worse than none: the AI (02) rule validates its check digit, so the whole
        payload then fails to decompose and the label cannot be scanned at all.
        """
        self.ensure_one()
        elements = []
        if self.product_id.default_code:
            elements.append(("240", self.product_id.default_code))
        if self.lot_id:
            elements.append(("10", self.lot_id.name))
        return elements

    @api.model
    def _get_gs1_qr_error(self, elements):
        """Say why these elements cannot be encoded, or return an empty string."""
        # GS1 "encodable character set 82", spelled exactly as Odoo's own AI (10)
        # rule pattern spells it so that what we print is what the nomenclature
        # parses back. Anchored \A to \Z rather than ^ to $: "$" also matches
        # before a trailing newline, and Char only trims in the web client, so a
        # reference imported with one would pass the check and then fail to
        # decompose.
        char_set_82 = re.compile(r'\A[!"%-/0-9:-?A-Z_a-z]+\Z')
        max_length = {"10": 20, "240": 30}
        # AI (240) is what identifies the product, so a payload without it cannot
        # be resolved to one. A lot on its own is not enough: AI (10) decomposes
        # on its own, so the label would look scannable and would only resolve
        # while that lot name happens to be unique across every product.
        if not any(ai == "240" for ai, _value in elements):
            return _("the product has no internal reference")
        for ai, value in elements:
            label = _("lot/serial") if ai == "10" else _("internal reference")
            if len(value) > max_length[ai]:
                return _(
                    "the %(label)s %(value)r is longer than the %(length)s "
                    "characters GS1 allows here",
                    label=label,
                    value=value,
                    length=max_length[ai],
                )
            if not char_set_82.match(value):
                return _(
                    "the %(label)s %(value)r uses characters GS1 cannot encode",
                    label=label,
                    value=value,
                )
        return ""

    @api.model
    def _get_gs1_qr_value(self, elements):
        # A keyboard wedge scanner cannot type the real FNC1 (0x1D) into a web
        # form, so the payload separates elements with "#", which
        # barcode.nomenclature accepts out of the box through the default
        # gs1_separator_fnc1 regex. "#" is outside character set 82, so it can
        # never occur inside an element value. Every element here is variable
        # length, so all but the last have to be closed with it, or the parser
        # reads the following AI as part of the value.
        fnc1 = "#"
        parts = []
        for index, (ai, value) in enumerate(elements):
            parts.append(ai + value)
            if index < len(elements) - 1:
                parts.append(fnc1)
        return "".join(parts)

    @api.model
    def _get_label_grid(self):
        # Keep in step with the cell size in the sheet template: 3 * 63.5mm
        # across and 7 * 38.1mm down.
        return 3, 7

    def _get_label_pages(self):
        """Lay the labels of these lines out as sheets of rows of cells."""
        columns, rows_per_page = self._get_label_grid()
        labels = [line for line in self for _ in range(max(line.label_qty, 0))]
        # A sheet that has already had labels peeled off it is filled from its
        # first free cell, so pad the front of the run with as many blanks. The
        # template prints an empty cell for each, which keeps the ones that
        # follow on the cells they are numbered for.
        start = max(self[:1].wizard_id.first_label_position, 1)
        cells = [False] * (start - 1) + labels
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
        # Which lines belong in the job depends on the format, so the list has to
        # be rebuilt when it changes: the base onchange fires on the report but
        # not on the format, and a line kept for a GS1 QR label has no barcode to
        # give the base template once the format is switched back off it.
        self._onchange_picking_ids()

    @api.model
    def _get_move_lines(self, picking):
        # The base module keeps only lines whose product has a barcode, which is
        # not what a GS1 QR label needs and hides the lines that cannot print.
        # List them all: the wizard says why each faulty one cannot be printed
        # and print_labels refuses, which beats dropping them without a word.
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
        # A label whose code cannot be built is worse than no label at all: it
        # looks complete, gets stuck on the goods, and only fails months later at
        # the count. Refuse the whole job and name the records to fix.
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
        """The lines the GS1 encoding check applies to."""
        if self.is_custom_label:
            return self.env["stock.picking.line.print"]
        # The sheet report always prints the symbol, whatever the format. The
        # format itself is a statement about the job rather than about one
        # report, so while it is selected the check holds for every report the
        # wizard can reach: a reference GS1 cannot encode is a record to fix
        # before any label of that job is stuck on the goods.
        if self.barcode_format == "gs1_qr" or self.barcode_report == self.env.ref(
            "stock_picking_product_barcode_report_gs1_qr.action_report_stock_qr_label"
        ):
            return self.product_print_moves.filtered(lambda line: line.label_qty > 0)
        return self.env["stock.picking.line.print"]

    @api.model
    def _prepare_data_from_move_line(self, move_line):
        values = super()._prepare_data_from_move_line(move_line)
        # At receipt the stock is not on its shelf yet, so the destination of the
        # move is the best "where is it now" the label can carry. Going out it is
        # the other way round: the destination is the customer or the vendor, and
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
        # super() builds exactly one command per lot, in browse order. A lot split
        # across shelves gets the first of them; printing per quant instead of per
        # lot is the way to label each shelf.
        for line, lot in zip(lines, lots):
            quants = lot.quant_ids.filtered(
                lambda quant: quant.location_id.usage == "internal" and quant.quantity
            )
            line[2]["location_id"] = quants[:1].location_id.id
        return lines
