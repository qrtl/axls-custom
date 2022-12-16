import base64
import json
import time
from logging import getLogger
from math import isnan

import requests

# For Pytest (インポートのフォルダ設定の問題でエラーになる?)
# from src.CheckerBase import CheckAvailability, PartInfo, SearchResult, Availability
from .checker_base import (
    ApiKeyInfo,
    Availability,
    CheckAvailability,
    LifeCycle,
    PartInfo,
    SearchResult,
)

_logger = getLogger(__name__)

NEXAR_URL = "https://api.nexar.com/graphql"
PROD_TOKEN_URL = "https://identity.nexar.com/connect/token"

ATTR_LIFECYCLE = "910"
ATTR_MFR_LIFECYCLE = "942"

NOT_FOUND = "Error"

QUERY_MPN = """
query Search($mpn: String!) {
    supSearchMpn(q: $mpn, limit: 2) {
      results {
        part {
          mpn
          octopartUrl
          shortDescription
          specs {
              attribute{
                  id
                  name
                  shortname
              }
              value
          }
          manufacturer {
            name
          }
          sellers(authorizedOnly: true) {
            company {
                name
            }
            isAuthorized
            offers {
                sku
                clickUrl
                inventoryLevel
                moq
                packaging
            }
          }
        }
      }
    }
  }
"""


def get_token(client_id, client_secret):
    """Return the Nexar token from the client_id and client_secret provided."""

    if not client_id or not client_secret:
        raise ConnectionRefusedError("client_id and/or client_secret are empty")

    token = {}
    try:
        token = requests.post(
            url=PROD_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            allow_redirects=False,
        ).json()
    except Exception:
        raise ConnectionRefusedError("Unable to connect NEXAR API.")

    if "error" in token:
        raise ConnectionRefusedError("Invalid client. Please check ID and Secret.")

    return token


def decodeJWT(token):
    return json.loads(
        (base64.urlsafe_b64decode(token.split(".")[1] + "==")).decode("utf-8")
    )


class OctpartCheckAvailability(CheckAvailability):
    def __init__(self, app_config: ApiKeyInfo) -> None:
        super().__init__(app_config)
        self._wait_sec = 0.1
        self._max_search_count_day = 0
        self._session = requests.session()
        self._session.keep_alive = False
        _logger.debug("Nexar API is initialized.")

    def initAPI(self):
        self._token = get_token(self._api_key.client_id, self._api_key.client_secret)
        self._session.headers.update({"token": self._token.get("access_token")})
        self._exp = decodeJWT(self._token.get("access_token")).get("exp")

    def availability(self, part_number: str) -> PartInfo:
        """Check part availability

        Args:
            part_number (str): part number for search

        Returns:
            PartInfo: search result
        """
        # Check part number nan / empty
        if isinstance(part_number, str) is False:
            if isnan(part_number):
                _logger.debug(f"P/N is nan: {part_number}")
                return PartInfo(
                    SearchResult.NotFound,
                    Availability.Other,
                    0,
                    "Empty",
                    {},
                    LifeCycle.Unknown,
                )
            elif part_number == "":
                _logger.debug(f"P/N is empty: {part_number}")
                return PartInfo(
                    SearchResult.NotFound,
                    Availability.Other,
                    0,
                    "Empty",
                    {},
                    LifeCycle.Unknown,
                )
        # Execute query
        data = self._do_search_octopart(part_number)
        part_info = self._check_availability(data, part_number)
        return part_info

    def _do_search_octopart(self, part_number: str) -> dict:
        variables = {"mpn": part_number}
        data = self.get_query(QUERY_MPN, variables)
        return data["supSearchMpn"]

    def _check_availability(self, data: dict, search_pn: str) -> PartInfo:
        # Partが None = 存在しないP/N
        if data["results"] is None:
            _logger.debug("Response does not have any result(s): " + str(search_pn))
            return PartInfo(
                SearchResult.NotFound,
                Availability.Other,
                0,
                NOT_FOUND,
                {},
                LifeCycle.Unknown,
                "",
            )

        # p/n そのものズバリは有るか?
        for result in data["results"]:
            if result["part"]["mpn"] == search_pn:
                avl = self._decode_availability(result["part"])
                status = self._check_lifecycle(result["part"])
                return PartInfo(
                    SearchResult.Exactly,
                    avl[0],
                    avl[1],
                    search_pn,
                    avl[2],
                    status,
                    result["part"]["octopartUrl"],
                )

        # なければ似た番号で在庫のあるもの(最初に該当したもの)
        for result in data["results"]:
            avl = self._decode_availability(result["part"])
            status = self._check_lifecycle(result["part"])
            return PartInfo(
                SearchResult.Similar,
                avl[0],
                avl[1],
                result["part"]["mpn"],
                avl[2],
                status,
                result["part"]["octopartUrl"],
            )
        # 何も見つからなかった
        return PartInfo(
            SearchResult.NotFound,
            Availability.Other,
            0,
            NOT_FOUND,
            {},
            LifeCycle.Unknown,
            "",
        )

    def _check_lifecycle(self, part: dict) -> LifeCycle:
        """specs の中からlifecycle の項目を探す
        Details: https://support.nexar.com/support/solutions/articles/101000434626-do-you-have-lifecycle-information-for-parts-

        Args:
            part (dict): part information

        Returns:
            LifeCycle: found status (Unknown is not matched)
        """
        for spec in part["specs"]:
            if spec["attribute"]["id"] == ATTR_LIFECYCLE:
                shortname = spec["value"]
                return LifeCycle(shortname)
        return LifeCycle.Unknown

    def _decode_availability(self, part: dict):
        stock_info = []
        total_inventory = 0
        for seller in part["sellers"]:
            # すべてのディストリビューターについて、名称と在庫のセットを取得
            company = seller["company"]["name"]
            inventory = 0
            for offer in seller["offers"]:
                # 在庫がなくても 1 が返ってくることが有る?
                if int(offer["inventoryLevel"]) > 1:
                    inventory = inventory + int(offer["inventoryLevel"])
            stock = {"company": company, "count": inventory}
            stock_info.append(stock)
            total_inventory = total_inventory + inventory
        # どのディストリビューターにも在庫がなかった
        if total_inventory == 0:
            return Availability.NotAvailable, 0, stock_info
        # どこかに在庫があった
        return Availability.Available, total_inventory, stock_info

    def get_query(self, query: str, variables: dict) -> dict:
        """Return Nexar response for the query."""
        _logger.debug(f"Query: {variables['mpn']}")
        try:
            self.check_exp()
            r = self._session.post(
                NEXAR_URL,
                json={"query": query, "variables": variables},
            )

        except Exception as e:
            _logger.error(f"Error while getting Nexar response:{e}")
            raise ConnectionAbortedError("Error while getting Nexar") from e

        response = r.json()
        if "errors" in response:
            for error in response["errors"]:
                _logger.error(error["message"])
            raise ConnectionAbortedError(
                f"Error in the response from Nexar API: {response['errors']}"
            )

        return response["data"]

    def check_exp(self):
        if self._exp < time.time() + 300:
            self._token = get_token(self._client_id, self._client_secret)
            self._session.headers.update({"token": self._token.get("access_token")})
            self._exp = decodeJWT(self._token.get("access_token")).get("exp")
