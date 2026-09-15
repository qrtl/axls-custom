# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

# The business domain the analytic distribution field of the purchase order
# header passes to the widget. Odoo declares none for it, while the field of
# the lines passes 'purchase_order' (see the core purchase views), so this is
# what tells the two apart. Mirrored in views/purchase_order_views.xml, which
# is where it is passed from.
HEADER_BUSINESS_DOMAIN = "purchase_order_header"


class AccountAnalyticPlan(models.Model):
    _inherit = "account.analytic.plan"

    def _get_applicability(self, **kwargs):
        """Keep the budget plan off the analytic distribution of the header.

        The distribution of the header is applied to every line of the order at
        once, while a budget number stands for a single line, so the plan
        holding the budget numbers has no business there. A plan that is
        unavailable is not a column of the analytic distribution widget at all,
        so the header can neither show a budget number nor set one.
        """
        self.ensure_one()
        if self.is_budget and kwargs.get("business_domain") == HEADER_BUSINESS_DOMAIN:
            return "unavailable"
        return super()._get_applicability(**kwargs)
