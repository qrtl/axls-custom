from enum import Enum
from logging import getLogger
from typing import Tuple

_logger = getLogger(__name__)


class SearchResult(Enum):
    Exactly = 1
    Similar = 2
    NotFound = 3


class Availability(Enum):
    Available = 1
    OnOrder = 2
    NotAvailable = 3
    Other = 4


class LifeCycle(Enum):
    EOL = "EOL"
    NRND = "NRND"
    New = "New"
    Obsolete = "Obsolete"
    Production = "Production"
    Unknown = "Unknown"


class StockAvailability(Enum):
    ExactlyAvailable = "extavl"
    ExactlyOnOrder = "extodr"
    ExactlyNotAvailable = "extnavl"
    SimilarAvailable = "simavl"
    SimilarOnOrder = "simodr"
    SimilarNotAvailable = "simnavl"
    NotFound = "notfnd"
    Unknown = "unknown"


class PartInfo:
    __slots__ = [
        "searchResult",
        "availability",
        "count",
        "part_number",
        "companies",
        "lifecycle",
        "octpartUrl",
    ]

    def __init__(
        self,
        searchResult: SearchResult,
        availability: Availability,
        count: int,
        part_number: str,
        companies: dict,
        lifecycle: LifeCycle,
        octpartUrl: str,
    ) -> None:
        self.searchResult = searchResult
        self.availability = availability
        self.count = count
        self.part_number = part_number
        self.companies = companies
        self.lifecycle = lifecycle
        self.octpartUrl = octpartUrl


class ApiKeyInfo:
    __slots__ = [
        "client_id",
        "client_secret",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret


class CheckAvailability:
    """部品存在確認用のベースクラス

    Returns:
        _type_: _description_
    """

    _api_key = ApiKeyInfo
    _wait_sec = float
    _max_search_count_day = int

    def __init__(self, api_key: ApiKeyInfo) -> None:
        self._api_key = api_key

    def availability(self, part_number: str) -> PartInfo:
        pass

    def minimum_search_wait_sec(self) -> float:
        """問い合わせ実行の最小限の待ち時間

        Returns:
            float: 最小待ち時間(Sec)
        """
        return float(self._wait_sec)

    def max_search_count_per_day(self) -> int:
        """一日に問い合わせ可能な最大件数

        Returns:
            int: 件数
        """
        return self._max_search_count_day

    def severity(self, partInfo: PartInfo) -> Tuple[StockAvailability, str]:
        if (
            partInfo.searchResult == SearchResult.Exactly
            and partInfo.availability == Availability.Available
        ):
            return StockAvailability.ExactlyAvailable, partInfo.part_number

        if (
            partInfo.searchResult == SearchResult.Exactly
            and partInfo.availability == Availability.OnOrder
        ):
            return StockAvailability.ExactlyOnOrder, partInfo.part_number

        if (
            partInfo.searchResult == SearchResult.Exactly
            and partInfo.availability == Availability.NotAvailable
        ):
            return StockAvailability.ExactlyNotAvailable, partInfo.part_number

        if (
            partInfo.searchResult == SearchResult.Similar
            and partInfo.availability == Availability.Available
        ):
            return StockAvailability.SimilarAvailable, partInfo.part_number

        if (
            partInfo.searchResult == SearchResult.Similar
            and partInfo.availability == Availability.OnOrder
        ):
            return StockAvailability.SimilarOnOrder, partInfo.part_number

        if (
            partInfo.searchResult == SearchResult.Similar
            and partInfo.availability == Availability.NotAvailable
        ):
            return StockAvailability.SimilarNotAvailable, partInfo.part_number

        if partInfo.part_number == "Empty":
            return StockAvailability.NotFound, partInfo.part_number

        if partInfo.searchResult == SearchResult.NotFound:
            return StockAvailability.NotFound, partInfo.part_number

        return StockAvailability.Unknown, ""
