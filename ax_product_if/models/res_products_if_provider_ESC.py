# Copyright 2022 Axelspace
# Other proprietary.
# Update from to はESCからのデータは無視することとする。

import logging
from collections import defaultdict
from zipfile import ZipFile

import pandas as pd

from odoo import fields, models

IF_FILE_LOCATION = "/mnt/ifdata/ifdata.zip"

_logger = logging.getLogger(__name__)


class ResProductsIfProviderESC(models.Model):

    _inherit = "res.products.if.provider"

    service = fields.Selection(
        selection_add=[("ESC", "IF from ESC")],
        ondelete={"ESC": "set default"},
    )

    def _obtain_products(self, date_from, date_to):
        # とりあえず日付は使わない
        self.ensure_one()
        if self.service != "ESC":
            return super()._obtain_products(date_from, date_to)  # pragma: no cover

        # ZIP内のCSVをまとめて開く
        Zip_file = ZipFile(IF_FILE_LOCATION)
        # 一列目をindexとして指定
        dfs = {
            text_file.filename: pd.read_csv(
                Zip_file.open(text_file.filename), index_col=0
            )
            for text_file in Zip_file.infolist()
            if text_file.filename.endswith(".csv")
        }

        # 辞書形式 {ESC ID: Name, Description} で返す
        content = defaultdict(dict)
        for file, df in dfs.items():
            if file == "eid.csv":
                df = df.drop(df.index[0])  # Remove 1st row
                df = df.drop("noUseFlag", axis=1)  # remove no use flag col
                df = df.drop("GenericName", axis=1)  # remove Generic Name col
                df["Category"] = "Electrical"
                df.columns = ["Name", "Description", "Category"]
                content.update(df.to_dict(orient="index"))
            if file == "pid.csv":
                df = df.drop(df.index[0])  # Remove 1st row
                df["Category"] = "Component"
                df.columns = ["Name", "Description", "Category"]
                content.update(df.to_dict(orient="index"))

        # _logger.info(content)
        return content
