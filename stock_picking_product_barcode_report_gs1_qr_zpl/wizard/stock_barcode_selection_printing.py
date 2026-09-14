# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import re

from odoo import _, models

ZPL_REPORT = (
    "stock_picking_product_barcode_report_gs1_qr_zpl.action_report_stock_qr_label_zpl"
)
# ZPL reads "^" and "~" as command introducers wherever they occur, field data
# included, so either one in a free-text value truncates the label instead of
# printing. Neither is in GS1 character set 82, so only the free-text fields --
# the product name and the shelf -- can ever carry one.
ZPL_CONTROL_CHARACTERS = re.compile(r"[\^~]")


class ProductPrintingQty(models.TransientModel):
    _inherit = "stock.picking.line.print"

    def _get_zpl_labels(self):
        """Return one entry per physical label.

        The sheet report pages its labels into a grid because it prints on A4;
        a roll printer has no grid, so the only thing left to expand here is
        the quantity asked for on the line.
        """
        return [line for line in self for _copy in range(max(line.label_qty, 0))]

    def _get_zpl_headers(self):
        """Return the row headers, kept out of the ZPL literal.

        The template body is t-translation="off" -- the ZPL commands around the
        values must never reach a .pot file -- and that also switches off
        translation for the headers sitting between them. Naming them here puts
        them back in the catalogue, with the same wording as the sheet label so
        the two can be compared side by side.
        """
        return {
            "purchase": _("PO"),
            "analytic": _("Subsidy"),
            "lot": _("S/N"),
            "shelf": _("Shelf"),
        }

    def _format_zpl(self, value):
        """Return a value that is safe to drop into a ^FD field."""
        return ZPL_CONTROL_CHARACTERS.sub(" ", value or "").replace("\n", " ").strip()


class WizStockBarcodeSelectionPrinting(models.TransientModel):
    _inherit = "stock.picking.print"

    def _get_gs1_qr_lines(self):
        # The ZPL label carries the same payload as the sheet, so it has to
        # refuse the same lines. Without this the wizard would happily send a
        # label with an empty ^BQ field to the printer, which is the failure
        # the sheet module exists to prevent.
        lines = super()._get_gs1_qr_lines()
        if lines or self.is_custom_label:
            return lines
        if self.barcode_report == self.env.ref(ZPL_REPORT):
            return self.product_print_moves.filtered(lambda line: line.label_qty > 0)
        return lines
