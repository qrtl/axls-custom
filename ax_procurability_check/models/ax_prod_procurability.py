# Copyright 2022 Axelspace
# License Other proprietary.

import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

from ..libs.octopart_checker import (
    NOT_FOUND,
    ApiKeyInfo,
    LifeCycle,
    OctpartCheckAvailability,
)

_logger = logging.getLogger(__name__)


class AxProdProcurability(models.Model):

    _name = "ax_prod_procurability"
    _description = "Ax product procurability information"
    _inherit = ["mail.thread"]
    _order = "name"

    name = fields.Char(string="Name", compute="_compute_name", store=True)
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self._default_company_id(),
    )
    product_id = fields.Many2one(
        "product.template",
        string="Product",
        ondelete="restrict",
        readonly=True,
        required=True,
    )
    product_name = fields.Char(
        "Product Name",
        related="product_id.name",
        readonly=True,
    )
    default_code = fields.Char(
        "Internal Reference",
        related="product_id.default_code",
        readonly=True,
    )
    categ_id = fields.Many2one(
        "product.category",
        string="Product Category",
        related="product_id.categ_id",
        ondelete="restrict",
        readonly=True,
    )
    stock_status = fields.Selection(
        [
            ("extavl", "Exactly Available"),
            ("extodr", "Exactly but OnOrder"),
            ("extnavl", "Exactly but Not Available"),
            ("simavl", "Similar Available"),
            ("simodr", "Similar but On Order"),
            ("simnavl", "Similar but Not Available"),
            ("notfnd", "Not Found"),
            ("unknown", "Unknown"),
        ],
        string="Stock Availability",
        default="unknown",
    )
    searched_pn = fields.Char(
        string="Searched P/N",
        readonly=True,
    )
    octopart_url = fields.Char(
        string="Stock info URL",
        readonly=False,
    )
    do_auto_check = fields.Boolean(
        string="Auto Check",
        default=True,
        readonly=False,
    )
    last_auto_update = fields.Datetime(
        string="Last Auto Update",
        readonly=True,
    )
    lifecycle = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("new", "NEW"),
            ("prod", "Production"),
            ("nrnd", "NRND"),
            ("eol", "EOL"),
            ("obs", "Obsolete"),
        ],
        default="unknown",
        string="Lifecycle(Auto)",
    )
    lifecycle_m = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("new", "NEW"),
            ("prod", "Production"),
            ("nrnd", "NRND"),
            ("eol", "EOL"),
            ("obs", "Obsolete"),
        ],
        default="unknown",
        string="Lifecycle(Manual)",
    )

    @api.depends("product_id")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.product_name}({record.default_code})"

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id

    @api.model
    def _update_execute(self):
        _logger.info("Scheduled procurability information update...")
        self.add_new_products()
        self.update_procurability_info()
        _logger.info("Scheduled procurability information update is completed.")

    def add_new_products(self):
        _logger.info("Going to add new products to the list...")
        products = self.env["product.template"].search([])
        _logger.info(f"Total {len(products)} items are going to process.")
        added_count = 0
        for product in products:
            if self.search(
                [
                    ("product_id", "=", product.id),
                ],
                limit=1,
            ):
                continue

            if product.name is not False and product.default_code is not False:
                # use sudo because a normal user
                # does not have access rights to ax_prod_procurability
                procurable_info = self.sudo().create(
                    {
                        "product_id": product.id,
                        "do_auto_check": True,
                    }
                )
                # update prod.template to add created procurable information
                product.procure_info_id = procurable_info.id
                added_count += 1
        _logger.info(f"Total {added_count} items are added.")

    def _restore_apikey(self) -> ApiKeyInfo:
        company_settings = self.env["res.company"].search(
            [("id", "=", self.env.company.id)]
        )
        return ApiKeyInfo(
            company_settings["octopart_client_id"],
            company_settings["octopart_client_secret"],
        )

    def _get_update_once(self) -> int:
        company_settings = self.env["res.company"].search(
            [("id", "=", self.env.company.id)]
        )
        update_once = company_settings["octopart_update_once"]
        if update_once <= 0:
            update_once = 50  # for safety mode if setting is under zero
        return update_once

    def update_procurability_info(self):
        _logger.info("Going to update procurability info...")
        checker = OctpartCheckAvailability(self._restore_apikey())
        try:
            checker.initAPI()
        except (ConnectionRefusedError, ConnectionAbortedError) as e:
            msg = _(f"Unable to initialize Octopart API: {e}")
            _logger.exception(msg)
            raise UserError(msg)

        target_list = self._find_update_target()
        if len(target_list) == 0:
            _logger.info("Nothing to be updated.")
            return

        _logger.info(f"Total {len(target_list)} records to be updating.")
        for procurability in target_list:
            try:
                with self.env.cr.savepoint():
                    result = checker.availability(procurability.product_name)
            except (ConnectionAbortedError) as e:
                _logger.warn(
                    f"API connection has failed during check {procurability.product_name}."
                    f"Please try again later:{e}"
                )
                continue

            _logger.info(
                f"{procurability.id}: {procurability.product_name} :"
                f" {result.lifecycle.name} / {result.searchResult.name} "
                f"/ {result.availability.name} / {result.count} pc as {result.part_number}"
                f" / {checker.severity(result)[0].value}"
            )
            if result.part_number == NOT_FOUND:
                _logger.info("Not in octpart")
                procurability.do_auto_check = False
                procurability.lifecycle = "unknown"
                procurability.last_auto_update = fields.Datetime.now()
            else:
                # update availability information
                procurability.do_auto_check = True
                if result.octpartUrl:
                    procurability.octopart_url = result.octpartUrl
                stock_status, pn = checker.severity(result)
                procurability.stock_status = stock_status.value
                procurability.searched_pn = pn
                if procurability.last_auto_update is False:
                    # 初回登録はLifecysle(手動)も合わせて更新
                    if result.lifecycle is LifeCycle.Production:
                        procurability.lifecycle = "prod"
                        procurability.lifecycle_m = "prod"
                    elif result.lifecycle is LifeCycle.Obsolete:
                        procurability.lifecycle = "obs"
                        procurability.lifecycle_m = "obs"
                    elif result.lifecycle is LifeCycle.EOL:
                        procurability.lifecycle = "eol"
                        procurability.lifecycle_m = "eol"
                    elif result.lifecycle is LifeCycle.New:
                        procurability.lifecycle = "new"
                        procurability.lifecycle_m = "new"
                    elif result.lifecycle is LifeCycle.NRND:
                        procurability.lifecycle = "nrnd"
                        procurability.lifecycle_m = "nrnd"
                    else:
                        procurability.lifecycle = "unknown"
                else:
                    # 2回目以降
                    if result.lifecycle is LifeCycle.Production:
                        procurability.lifecycle = "prod"
                    elif result.lifecycle is LifeCycle.Obsolete:
                        procurability.lifecycle = "obs"
                    elif result.lifecycle is LifeCycle.EOL:
                        procurability.lifecycle = "eol"
                    elif result.lifecycle is LifeCycle.New:
                        procurability.lifecycle = "new"
                    elif result.lifecycle is LifeCycle.NRND:
                        procurability.lifecycle = "nrnd"
                    else:
                        procurability.lifecycle = "unknown"
                procurability.last_auto_update = fields.Datetime.now()

    def _find_update_target(self):
        # 自動チェック対象のもの、かつ、
        # 一度も自動更新されていない物を優先
        target_list = self.search(
            [
                "&",
                ("do_auto_check", "=", True),
                ("last_auto_update", "=", False),
            ],
            limit=self._get_update_once(),
        )
        if target_list:
            return target_list

        # 過去一ヶ月間で更新されているものは除外
        # 最も古い最終更新日時以降でXX件(設定から読み込み)を更新対象とする
        month_ago = fields.Datetime.now() - relativedelta(months=1)
        # month_ago = fields.Datetime.now()  # for debug
        target_list = self.search(
            [
                "&",
                ("do_auto_check", "=", True),
                ("last_auto_update", "<", month_ago),
            ],
            order="last_auto_update asc",
            limit=self._get_update_once(),
        )
        return target_list
