# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from contextlib import contextmanager

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    company_amount = fields.Monetary(
        string="Company Currency Amount",
        currency_field="company_currency_id",
        help="Company-currency value you actually paid for this line. When "
        "set, the line's balance is forced to this amount instead of the "
        "standard amount_currency / exchange_rate conversion, while the "
        "foreign-currency amount stays untouched. Enter it unsigned -- the "
        "debit/credit direction follows the line's foreign-currency amount. "
        "Leave it empty to keep the standard conversion. Only available on "
        "the deposit line of a vendor bill taking part in a purchase-deposit "
        "flow; every other line follows from it automatically.",
    )
    company_amount_allowed = fields.Boolean(
        compute="_compute_company_amount_allowed",
        help="Technical field driving the read-only state of "
        "'Company Currency Amount' in the form view: True when this line "
        "belongs to a vendor bill that carries a purchase deposit, which is "
        "the only situation where the override is accepted.",
    )

    @api.depends(
        "display_type",
        "purchase_line_id.is_deposit",
        "quantity",
        "move_id.move_type",
        "move_id.line_ids.display_type",
        "move_id.line_ids.purchase_line_id.is_deposit",
    )
    def _compute_company_amount_allowed(self):
        for line in self:
            line.company_amount_allowed = line._is_company_amount_allowed()

    @api.constrains(
        "company_amount", "display_type", "purchase_line_id", "quantity", "move_id"
    )
    def _check_company_amount_allowed(self):
        for line in self.filtered("company_amount"):
            if line._is_company_amount_allowed():
                continue
            raise ValidationError(
                _(
                    "'%(field)s' can only be set on a vendor bill that carries "
                    "a purchase deposit. On line '%(line)s' of '%(move)s' the "
                    "standard exchange-rate conversion applies; clear the value "
                    "to continue."
                )
                % {
                    "field": line._fields["company_amount"].string,
                    "line": line.name or line.product_id.display_name or "/",
                    "move": line.move_id.display_name,
                }
            )

    @contextmanager
    def _sync_invoice(self, container):
        """Re-pin overridden balances once the standard invoice sync has run.

        This is the module's single write path. ``_sync_invoice`` is the exact
        point where Odoo turns ``amount_currency`` into ``balance`` for invoice
        lines, and it deliberately leaves ``balance`` alone when someone else
        has already written it -- so applying the override here, on the way
        out, survives the standard computation instead of racing it.

        Ordering matters and is what makes the payable come out right:
        ``account.move._sync_dynamic_lines`` enters the payment-term sync
        *before* this one, so it exits *after* it, and rebuilds the payable
        from the balances written here rather than from the rate-converted
        ones. See ``account.move._apply_company_amount_overrides`` for why
        that rebuild has to be prompted rather than left to happen.
        """
        with super()._sync_invoice(container):
            yield
        if self.env.context.get("skip_company_amount_sync"):
            return
        lines = container["records"].with_context(skip_company_amount_sync=True)
        lines.move_id._apply_company_amount_overrides()

    def _is_company_amount_allowed(self):
        """Only the deposit line itself may be pinned by hand.

        What is known outside Odoo is the amount paid for the deposit, so that
        is the only line worth typing on. The rest of the bill follows from it:
        the goods lines take the rate difference automatically, and the offset
        line on the final bill is read back from the posted deposit bill.

        The positive quantity is what confines this to the deposit bill: the
        final bill's offset reuses the same deposit purchase order line with a
        negative quantity, and its value is read back from the posted deposit
        bill rather than typed. So this stays a property of the line alone and
        needs no look at ``account.move.is_deposit``, which the conditions
        below already imply.
        """
        self.ensure_one()
        return (
            self.move_id.move_type in ("in_invoice", "in_refund")
            and self.display_type == "product"
            and bool(self.purchase_line_id.is_deposit)
            and self.quantity > 0
        )

    def _get_rate_based_balance(self):
        """Company-currency value this line would carry with no override, i.e.
        what the standard invoice sync computes. Deriving every target from
        this -- never from the current ``balance`` -- is what keeps the
        override idempotent when the sync runs more than once per write.
        """
        self.ensure_one()
        if not self.currency_rate:
            return self.balance
        return self.company_currency_id.round(self.amount_currency / self.currency_rate)

    def _get_gross_unit_price(self):
        """Let the price-difference logic see the overridden company-currency
        value, so both the price-difference journal item and the
        ``stock.valuation.layer`` adjustment reflect what was really paid.

        This acts on the *goods* line of the bill, never on the deposit line:
        ``purchase_deposit`` requires the deposit product to be a service, so
        it carries no valuation layer and the caller skips it. The goods line
        is the one whose balance absorbed the deposit's rate difference, which
        is exactly what has to reach the stock valuation.

        Standard computes ``price_subtotal / quantity`` in document currency,
        and the caller converts back with ``/ currency_rate``. Since
        ``price_subtotal`` is ``balance * currency_rate`` on a bill and its
        negation on a refund -- the same negation standard then applies -- the
        override is that formula with the overridden balance substituted in,
        and needs no sign handling of its own.
        """
        res = super()._get_gross_unit_price()
        if float_is_zero(
            self.quantity, precision_rounding=self.product_uom_id.rounding
        ):
            return res
        # Gate on the move netting off a deposit, not on ``is_deposit``: the
        # goods line lives on the *final* bill, which is not itself a deposit
        # bill. Nor on whether this line may be edited -- it may not, and its
        # balance is pinned all the same.
        if (
            self.currency_id == self.company_currency_id
            or not self.move_id._get_deposit_offset_lines()
        ):
            return res
        if self.company_currency_id.is_zero(
            self.balance - self._get_rate_based_balance()
        ):
            return res
        return self.balance / self.quantity * self.currency_rate
