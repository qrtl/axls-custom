# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AnalyticBudgetAttribute(models.AbstractModel):
    """What the four attributes of a budget number have in common.

    Each attribute is a model of its own, so that its values are maintained as
    master data instead of retyped as free text on every analytic account.
    """

    _name = "analytic.budget.attribute"
    _description = "Analytic Budget Attribute"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(
        default=True,
        help="Archived values stay on the analytic accounts that carry them, "
        "but cannot be picked any more.",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "This name is already taken. Two values of the same name could not "
            "be told apart on an analytic account.",
        )
    ]


class AnalyticBudgetSatellite(models.Model):
    _name = "analytic.budget.satellite"
    _inherit = "analytic.budget.attribute"
    _description = "Budget Satellite"


class AnalyticBudgetSubsystem(models.Model):
    _name = "analytic.budget.subsystem"
    _inherit = "analytic.budget.attribute"
    _description = "Budget Subsystem"


class AnalyticBudgetComponent(models.Model):
    _name = "analytic.budget.component"
    _inherit = "analytic.budget.attribute"
    _description = "Budget Component"


class AnalyticBudgetModel(models.Model):
    _name = "analytic.budget.model"
    _inherit = "analytic.budget.attribute"
    _description = "Budget Model"
