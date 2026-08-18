# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from contextlib import contextmanager

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
        "vendor bills that take part in a purchase-deposit flow.",
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
        "move_id.move_type",
        "move_id.line_ids.display_type",
        "move_id.line_ids.purchase_line_id.is_deposit",
    )
    def _compute_company_amount_allowed(self):
        for line in self:
            line.company_amount_allowed = line._is_company_amount_allowed()

    @api.constrains("company_amount", "display_type", "purchase_line_id", "move_id")
    def _check_company_amount_allowed(self):
        """Reject an override on a line that is not entitled to one.

        Constrained on the fields the check actually reads, so writing any of
        them re-validates. The companion constraint on ``account.move`` catches
        the other half -- lines being added to or removed from the move, which
        changes the answer without touching any field here.
        """
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
        """The override only makes sense inside the ``purchase_deposit`` flow.

        Two cases qualify, and both are recognised by the presence of a deposit
        line on the move itself:

        * the deposit vendor bill -- it holds the positive deposit line whose
          company-currency value the user wants to pin;
        * the final invoice -- it holds the negative deposit-offset line, and
          its product lines absorb the deposit's rate difference.

        On any other vendor bill the standard ``amount_currency /
        currency_rate`` conversion applies, unchanged.
        """
        self.ensure_one()
        if self.move_id.move_type not in ("in_invoice", "in_refund"):
            return False
        if self.display_type != "product":
            return False
        return bool(
            self.move_id.line_ids.filtered(
                lambda l: l.display_type == "product" and l.purchase_line_id.is_deposit
            )
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
        """Let ``purchase_stock``'s price-difference logic see the overridden
        company-currency value, so both the price-difference AML and the
        ``stock.valuation.layer`` adjustment reflect what was really paid.

        The caller divides this back down by the rate, so we scale the
        effective balance up by ``currency_rate`` to land on
        ``balance / quantity`` in company currency.
        """
        res = super()._get_gross_unit_price()
        if not (
            self.quantity
            and self.currency_rate
            and self.currency_id != self.company_currency_id
            and self._is_company_amount_allowed()
        ):
            return res
        rate_based = self._get_rate_based_balance()
        if self.company_currency_id.is_zero(self.balance - rate_based):
            return res
        sign = -1 if self.move_id.move_type == "in_refund" else 1
        return abs(self.balance) / self.quantity * self.currency_rate * sign
