import asyncpg
from hydra.data.storage.base import Candle, OhlcvStore

_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv (
    market    TEXT    NOT NULL,
    symbol    TEXT    NOT NULL,
    timeframe TEXT    NOT NULL,
    open_time BIGINT  NOT NULL,
    open      DOUBLE PRECISION NOT NULL,
    high      DOUBLE PRECISION NOT NULL,
    low       DOUBLE PRECISION NOT NULL,
    close     DOUBLE PRECISION NOT NULL,
    volume    DOUBLE PRECISION NOT NULL,
    close_time BIGINT NOT NULL,
    PRIMARY KEY (market, symbol, timeframe, open_time)
);
CREATE INDEX IF NOT EXISTS idx_ohlcv_lookup
    ON ohlcv (market, symbol, timeframe, open_time);
"""


class PostgresStore(OhlcvStore):
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def init(self) -> None:
        self._pool = await asyncpg.create_pool(self._dsn)
        async with self._pool.acquire() as conn:
            await conn.execute(_DDL)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def upsert(self, candles: list[Candle]) -> None:
        if not candles or self._pool is None:
            return
        rows = [
            (c.market, c.symbol, c.timeframe, c.open_time,
             c.open, c.high, c.low, c.close, c.volume, c.close_time)
            for c in candles
        ]
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO ohlcv
                   (market, symbol, timeframe, open_time, open, high, low, close, volume, close_time)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                   ON CONFLICT (market, symbol, timeframe, open_time) DO UPDATE
                   SET open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
                       close=EXCLUDED.close, volume=EXCLUDED.volume, close_time=EXCLUDED.close_time""",
                rows,
            )

    async def query(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        limit: int = 200,
        since: int | None = None,
    ) -> list[Candle]:
        if self._pool is None:
            return []
        if since is not None:
            sql = (
                "SELECT * FROM ohlcv WHERE market=$1 AND symbol=$2 AND timeframe=$3 "
                "AND open_time>=$4 ORDER BY open_time ASC LIMIT $5"
            )
            params = (market, symbol, timeframe, since, limit)
        else:
            sql = (
                "SELECT * FROM ohlcv WHERE market=$1 AND symbol=$2 AND timeframe=$3 "
                "ORDER BY open_time ASC LIMIT $4"
            )
            params = (market, symbol, timeframe, limit)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
        return [
            Candle(
                market=r["market"], symbol=r["symbol"], timeframe=r["timeframe"],
                open_time=r["open_time"], open=r["open"], high=r["high"],
                low=r["low"], close=r["close"], volume=r["volume"], close_time=r["close_time"],
            )
            for r in rows
        ]

    async def get_symbols(self) -> list[dict]:
        if self._pool is None:
            return []
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT market, symbol, timeframe FROM ohlcv ORDER BY market, symbol, timeframe"
            )
        return [{"market": r["market"], "symbol": r["symbol"], "timeframe": r["timeframe"]} for r in rows]
