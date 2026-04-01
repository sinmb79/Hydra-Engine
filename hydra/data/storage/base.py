from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Candle:
    market: str
    symbol: str
    timeframe: str
    open_time: int   # Unix ms
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int  # Unix ms


class OhlcvStore(ABC):
    @abstractmethod
    async def init(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def upsert(self, candles: list[Candle]) -> None: ...

    @abstractmethod
    async def query(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        limit: int = 200,
        since: int | None = None,
    ) -> list[Candle]: ...

    @abstractmethod
    async def get_symbols(self) -> list[dict]: ...
