# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class SVLReportCategory(models.Model):
    _name = "svl.report.category"
    _description = "SVL Report Category"
    _order = "sequence, id"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    domain = fields.Char()
    is_other = fields.Boolean(string="Other Category")
    report_type = fields.Selection(
        [
            ("storable", "Storable"),
            ("consumable", "Consumable"),
            ("both", "Both"),
        ],
        default="both",
        required=True,
    )

    def _get_domain(self):
        self.ensure_one()
        if not self.domain:
            return []
        return safe_eval(self.domain)

    @api.constrains("domain")
    def _check_domain(self):
        for record in self:
            if not record.domain:
                continue
            try:
                safe_eval(record.domain)
            except Exception as exc:
                raise ValidationError(
                    _("Invalid domain for category '%(category)s': %(error)s")
                    % {
                        "category": record.display_name,
                        "error": exc,
                    }
                ) from exc

    @api.constrains("is_other", "active")
    def _check_unique_other_category(self):
        for record in self:
            if not record.is_other or not record.active:
                continue
            existing = self.search(
                [
                    ("id", "!=", record.id),
                    ("is_other", "=", True),
                ],
                limit=1,
            )
            if existing:
                raise ValidationError(
                    _(
                        "Only one 'Other Category' is allowed."
                        "Deactivate the existing one or unset 'Other Category'."
                    )
                )
