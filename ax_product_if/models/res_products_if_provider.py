# Copyright 2022 Axelspace
# Other proprietary.

import logging
from datetime import datetime, time

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResProductsIfProvider(models.Model):

    _name = "res.products.if.provider"
    _description = "Products interface provider"
    _inherit = ["mail.thread"]
    _order = "name"

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self._default_company_id(),
    )
    active = fields.Boolean(default=True)
    service = fields.Selection(
        string="Source Service",
        selection=[("none", "None")],
        default="none",
        required=True,
    )
    name = fields.Char(string="Name", compute="_compute_name", store=True)
    interval_type = fields.Selection(
        string="Units of scheduled update interval",
        selection=[("days", "Day(s)"), ("weeks", "Week(s)"), ("months", "Month(s)")],
        default="days",
        required=True,
    )
    interval_number = fields.Integer(
        string="Scheduled update interval", default=1, required=True
    )
    update_schedule = fields.Char(
        string="Update Schedule", compute="_compute_update_schedule"
    )
    last_successful_run = fields.Date(string="Last successful update")
    next_run = fields.Date(
        string="Next scheduled update", default=fields.Date.today, required=True
    )

    _sql_constraints = [
        (
            "service_company_id_uniq",
            "UNIQUE(service, company_id)",
            "Service can only be used in one provider per company!",
        ),
        (
            "valid_interval_number",
            "CHECK(interval_number > 0)",
            "Scheduled update interval must be greater than zero!",
        ),
    ]

    @api.model
    def _default_company_id(self):
        return self.env["res.company"]._company_default_get()

    def _update(self, date_from, date_to, newest_only=False):
        is_scheduled = self.env.context.get("scheduled")
        Products = self.env["product.product"]
        for provider in self:
            try:
                # 辞書形式 {ESC ID: Name, Description} で返ってくる
                data = provider._obtain_products(
                    date_from,
                    date_to,
                ).items()
            except BaseException as e:
                _logger.warning(
                    'Products IF Provider "%s" failed to obtain data since'
                    " %s until %s"
                    % (
                        provider.name,
                        date_from,
                        date_to,
                    ),
                    exc_info=True,
                )
                provider.message_post(
                    subject=_("Products IF Provider Failure"),
                    body=_(
                        'Products IF Provider "%s" failed to obtain data'
                        " since %s until %s:\n%s"
                    )
                    % (
                        provider.name,
                        date_from,
                        date_to,
                        str(e) if e else _("N/A"),
                    ),
                )
                continue

            if not data:
                if is_scheduled:
                    provider._schedule_next_run()
                continue
            # if newest_only:
            #    data = [max(data, key=lambda x: fields.Date.from_string(x[0]))]

            # ここでProduct登録する
            for default_code, product_info in data:
                product = Products.search(
                    [("default_code", "=", default_code)], limit=1
                )
                if not product:
                    # _logger.info("No default_code. Add new product:" + str(default_code))
                    self._add_new_product(
                        provider, Products, default_code, product_info
                    )

            if is_scheduled:
                provider._schedule_next_run()

    def _add_new_product(self, provider, Products, default_code, product_info):
        category = self._get_prod_cat_id(product_info["Category"])
        Products.create(
            {
                "company_id": provider.company_id.id,
                "name": product_info["Name"],
                "default_code": default_code,
                "type": "product",
                "categ_id": category.id,
                "sale_ok": False,
                "purchase_ok": True,
                "description": product_info["Description"],
            }
        )

    def _get_prod_cat_id(self, cat_name):
        category = self.env["product.category"].search(
            [("name", "=", cat_name)], limit=1
        )
        if category:
            return category
        else:
            raise UserError(
                _("Category %(cat_name)s does not exist") % {"cat_name": cat_name}
            )

    def _schedule_next_run(self):
        self.ensure_one()
        self.last_successful_run = fields.Date.context_today(self)
        self.next_run = (
            datetime.combine(self.next_run, time.min) + self._get_next_run_period()
        ).date()

    @api.depends("service")
    def _compute_name(self):
        for provider in self:
            provider.name = list(
                filter(
                    lambda x: x[0] == provider.service,
                    self._fields["service"].selection,
                )
            )[0][1]

    @api.depends("active", "interval_type", "interval_number")
    def _compute_update_schedule(self):
        for provider in self:
            if not provider.active:
                provider.update_schedule = _("Inactive")
                continue

            provider.update_schedule = _("%(number)s %(type)s") % {
                "number": provider.interval_number,
                "type": list(
                    filter(
                        lambda x: x[0] == provider.interval_type,
                        self._fields["interval_type"].selection,
                    )
                )[0][1],
            }

    @api.model
    def _scheduled_update(self):
        _logger.info("Scheduled products interface update...")

        providers = self.search(
            [
                ("company_id.product_interface", "=", True),
                ("active", "=", True),
                ("next_run", "<=", fields.Date.context_today(self)),
            ]
        )
        _logger.info("date today in context: " + str(fields.Date.context_today(self)))
        if providers:
            _logger.info(
                "Scheduled products interface update of: %s"
                % ", ".join(providers.mapped("name"))
            )
            for provider in providers.with_context({"scheduled": True}):
                date_from = (
                    (provider.last_successful_run + relativedelta(days=1))
                    if provider.last_successful_run
                    else (provider.next_run - provider._get_next_run_period())
                )
                date_to = provider.next_run
                provider._update(date_from, date_to, newest_only=True)

        _logger.info("Scheduled products interface update complete.")

    def _get_next_run_period(self):
        self.ensure_one()

        if self.interval_type == "days":
            return relativedelta(days=self.interval_number)
        elif self.interval_type == "weeks":
            return relativedelta(weeks=self.interval_number)
        elif self.interval_type == "months":
            return relativedelta(months=self.interval_number)

    def _obtain_products(self, date_from, date_to):
        # pragma: no cover
        self.ensure_one()
        return {}
