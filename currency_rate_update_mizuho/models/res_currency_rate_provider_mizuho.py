# Copyright 2022 Axelspace
# Copyright 2022 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import csv
from io import StringIO

import requests

from odoo import api, fields, models


class ResCurrencyRateProviderMizuho(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("mizuho", "Mizuho Bank (Japan)")],
        ondelete={"mizuho": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "mizuho":
            return super()._get_supported_currencies()
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

    @api.model
    def _is_in_this_month(self, date_from, date_to):
        d_today = fields.Date.context_today(self)
        ym_from = date_from.year + date_from.month
        ym_to = date_to.year + date_to.month
        ym_now = d_today.year + d_today.month
        if ym_from == ym_to == ym_now:
            return True
        return False

    def _get_mizuho_rates(self, url, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        daily_rates = {}
        response = requests.get(url=url, timeout=10)
        response.encoding = response.apparent_encoding
        csv_iterator = csv.reader(StringIO(response.text), delimiter=",")
        next(csv_iterator)
        next(csv_iterator)
        # Field labels are on the third row.
        field_labels = next(csv_iterator)
        invert = False
        if base_currency != "JPY":
            invert = True
            if base_currency not in currencies:
                currencies.append(base_currency)
        for row in csv_iterator:
            # Change date format
            row_date = row[0].replace("/", "-")
            row_date_date = fields.Date.to_date(row_date)
            if row_date_date < date_from or row_date_date > date_to:
                continue
            daily_rates[row_date] = {}
            for currency in currencies:
                row_curr_rate = row[field_labels.index(currency)]
                daily_rates[row_date][currency] = 1 / float(row_curr_rate)
        if invert:
            for k in daily_rates.keys():
                base_rate = daily_rates[k][base_currency]
                for curr in daily_rates[k].keys():
                    daily_rates[k][curr] = daily_rates[k][curr] / base_rate
                daily_rates[k]["JPY"] = 1.0 / base_rate
        return daily_rates

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "mizuho":
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)
        # Depending on the date range, different URLs are used
        url = "https://www.mizuhobank.co.jp/market/csv"
        if self._is_in_this_month(date_from, date_to):
            url = url + "/tm_quote.csv"
        else:
            url = url + "/quote.csv"
        return self._get_mizuho_rates(
            url, base_currency, currencies, date_from, date_to
        )
