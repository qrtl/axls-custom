# Copyright 2022 Axelspace
# Copyright 2022 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import csv
import xml.etree.ElementTree as et
import xml.sax
from collections import defaultdict
from datetime import date, datetime
from io import StringIO

import requests

from odoo import fields, models


class ResCurrencyRateProviderMizuho(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("Mizuho", "Mizuho Bank (Japan)")],
        ondelete={"Mizuho": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "Mizuho":
            return super()._get_supported_currencies()  # pragma: no cover
        # List of currencies obrained from:
        # https://www.mizuhobank.co.jp/market/historical.html
        return [
            "USD",
            "GBP",
            "EUR",
            "CAD",
            "CHF",
            "SEK",
            "DKK",
            "NOK",
            "AUD",
            "NZD",
            "ZAR",
            "BHD",
            "CNY",
            "HKD",
            "INR",
            "MYR",
            "PHP",
            "SGD",
            "THB",
            "KWD",
            "SAR",
            "AED",
            "MXN",
            "PGK",
            "HUF",
            "CZK",
            "PLN",
            "TRY",
        ]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "Mizuho":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover
        invert_calculation = False
        if base_currency != "JPY":
            invert_calculation = True
            if base_currency not in currencies:
                currencies.append(base_currency)
        # Depending on the date range, different URLs are used
        url = "https://www.mizuhobank.co.jp/market/csv"
        if self._Is_in_this_month(date_from, date_to):
            url = url + "/tm_quote.csv"
        else:
            url = url + "/quote.csv"
        handler = RatesHandler(currencies, date_from, date_to)
        xml.sax.parseString(self._get_mizuho_rates(url, date_from), handler)
        content = handler.content
        if invert_calculation:
            for k in content.keys():
                base_rate = float(content[k][base_currency])
                for rate in content[k].keys():
                    content[k][rate] = str(float(content[k][rate]) / base_rate)
                content[k]["JPY"] = str(1.0 / base_rate)
        return content

    def _get_mizuho_rates(self, url: str, date_from: date) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36"
        }
        response = requests.get(url=url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding
        # Read CSV and adjustment
        data = csv.reader(StringIO(response.text), delimiter=",")
        next(data)
        next(data)
        list_of_column_names = []
        for row in data:
            # adding the first row as column
            list_of_column_names.append(row)
            # breaking the loop after the
            # first iteration itself
            break
        if list_of_column_names:
            # Add first column name to Date
            list_of_column_names[0][0] = "Date"
        next(data)
        # convert to XML
        root = et.Element("root")
        elm1 = et.Element("Cube")
        root.append(elm1)
        for row in data:
            # Change date format
            row[0] = row[0].replace("/", "-")
            row[0] = datetime.strptime(row[0], "%Y-%m-%d").date()
            if row[0] < date_from:
                continue
            sub_eml = et.SubElement(elm1, "Cube", attrib={"time": str(row[0])})
            for j, colName in enumerate(list_of_column_names[0]):
                if colName == "Date" or colName == "":
                    continue
                if str(row[j]) == "*****":
                    continue
                et.SubElement(
                    sub_eml,
                    "Cube",
                    attrib={"currency": colName, "rate": str(1 / float(row[j]))},
                )
        return et.tostring(root)

    def _Is_in_this_month(self, date_from: date, date_to: date):
        d_today = date.today()
        ym_from = date_from.year + date_from.month
        ym_to = date_to.year + date_to.month
        ym_now = d_today.year + d_today.month
        if ym_from == ym_to == ym_now:
            return True
        else:
            return False


class RatesHandler(xml.sax.ContentHandler):
    def __init__(self, currencies, date_from, date_to):
        self.currencies = currencies
        self.date_from = date_from
        self.date_to = date_to
        self.date = None
        self.content = defaultdict(dict)

    def startElement(self, name, attrs):
        if name == "Cube" and "time" in attrs:
            self.date = fields.Date.from_string(attrs["time"])
        elif name == "Cube" and all([x in attrs for x in ["currency", "rate"]]):
            currency = attrs["currency"]
            rate = attrs["rate"]
            if (
                (self.date_from is None or self.date >= self.date_from)
                and (self.date_to is None or self.date <= self.date_to)
                and currency in self.currencies
            ):
                self.content[self.date.isoformat()][currency] = rate
