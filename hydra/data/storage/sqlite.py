import aiosqlite
from hydra.data.storage.base import Candle, OhlcvStore

_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv (
    market    TEXT    NOT NULL,
    symbol    TEXT    NOT NULL,
    timeframe TEXT    NOT NULL,
    open_time INTEGER NOT NULL,
    open      REAL    NOT NULL,
    high      REAL    NOT NULL,
    low       REAL    NOT NULL,
    close     REAL    NOT NULL,
    volume    REAL    NOT NULL,
    close_time INTEGER NOT NULL,
    PRIMARY KEY (market, symbol, timeframe, open_time)
);
CREATE INDEX IF NOT EXISTS idx_ohlcv_lookup
    ON ohlcv (market, symbol, timeframe, open_time);
"""


class SQLiteStore(OhlcvStore):
    def __init__(self, path: str) -> None:
        self._path = path
        self._db: aiosqlite.Connection | None = None

    async def init(self) -> None:
        import os
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_DDL)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def upsert(self, candles: list[Candle]) -> None:
        if not candles or self._db is None:
            return
        rows = [
            (c.market, c.symbol, c.timeframe, c.open_time,
             c.open, c.high, c.low, c.close, c.volume, c.close_time)
            for c in candles
        ]
        await self._db.executemany(
            """INSERT OR REPLACE INTO ohlcv
               (market, symbol, timeframe, open_time, open, high, low, close, volume, close_time)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        await self._db.commit()

    async def query(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        limit: int = 200,
        since: int | None = None,
    ) -> list[Candle]:
        if self._db is None:
            return []
        if since is not None:
            sql = (
                "SELECT * FROM ohlcv WHERE market=? AND symbol=? AND timeframe=? "
                "AND open_time>=? ORDER BY open_time ASC LIMIT ?"
            )
            params = (market, symbol, timeframe, since, limit)
        else:
            sql = (
                "SELECT * FROM ohlcv WHERE market=? AND symbol=? AND timeframe=? "
                "ORDER BY open_time ASC LIMIT ?"
            )
            params = (market, symbol, timeframe, limit)
        async with self._db.execute(sql, params) as cur:
            rows = await cur.fetchall()
        return [
            Candle(
                market=r["market"],
                symbol=r["symbol"],
                timeframe=r["timeframe"],
                open_time=r["open_time"],
                open=r["open"],
                high=r["high"],
                low=r["low"],
                close=r["close"],
                volume=r["volume"],
                close_time=r["close_time"],
            )
            for r in rows
        ]

    async def get_symbols(self) -> list[dict]:
        if self._db is None:
            return []
        sql = "SELECT DISTINCT market, symbol, timeframe FROM ohlcv ORDER BY market, symbol, timeframe"
        async with self._db.execute(sql) as cur:
            rows = await cur.fetchall()
        return [{"market": r["market"], "symbol": r["symbol"], "timeframe": r["timeframe"]} for r in rows]
