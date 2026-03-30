import json
import time
from datetime import date
from typing import Optional

from hydra.logging.setup import get_logger

logger = get_logger(__name__)

PNL_REALIZED_KEY = "hydra:pnl:realized:total"
PNL_TRADE_COUNT_KEY = "hydra:pnl:trade_count"


def _daily_key() -> str:
    return f"hydra:pnl:daily:{date.today().isoformat()}"


class PnlTracker:
    """
    시스템 전체 손익 추적.
    - 실현 손익: 포지션 청산 시 record_trade()로 기록
    - 미실현 손익: 포지션 데이터(mark_price)로 계산
    """

    def __init__(self, redis_client):
        self._redis = redis_client

    # ─── 실현 손익 ───────────────────────────────────────────────

    def record_trade(self, market: str, symbol: str, realized_pnl: float) -> None:
        """포지션 청산 시 실현 손익 기록."""
        pipe = self._redis.pipeline()
        pipe.incrbyfloat(PNL_REALIZED_KEY, realized_pnl)
        pipe.incrbyfloat(_daily_key(), realized_pnl)
        pipe.incr(PNL_TRADE_COUNT_KEY)
        # 개별 심볼 실현 손익
        pipe.incrbyfloat(f"hydra:pnl:symbol:{market}:{symbol}", realized_pnl)
        pipe.execute()
        logger.info("pnl_recorded", market=market, symbol=symbol, realized_pnl=realized_pnl)

    def get_realized_total(self) -> float:
        raw = self._redis.get(PNL_REALIZED_KEY)
        return float(raw) if raw else 0.0

    def get_daily_realized(self) -> float:
        raw = self._redis.get(_daily_key())
        return float(raw) if raw else 0.0

    def get_trade_count(self) -> int:
        raw = self._redis.get(PNL_TRADE_COUNT_KEY)
        return int(raw) if raw else 0

    def get_symbol_realized(self, market: str, symbol: str) -> float:
        raw = self._redis.get(f"hydra:pnl:symbol:{market}:{symbol}")
        return float(raw) if raw else 0.0

    # ─── 미실현 손익 ──────────────────────────────────────────────

    @staticmethod
    def calc_unrealized(position: dict) -> float:
        """단일 포지션의 미실현 손익 계산.
        position dict: {qty, avg_price, mark_price, side, leverage}
        """
        qty = float(position.get("qty", 0))
        avg_price = float(position.get("avg_price", 0))
        mark_price = float(position.get("mark_price", avg_price))
        side = position.get("side", "buy")
        leverage = float(position.get("leverage", 1))

        if qty == 0 or avg_price == 0:
            return 0.0

        price_diff = mark_price - avg_price
        if side == "sell":
            price_diff = -price_diff

        return price_diff * qty * leverage

    def get_unrealized_total(self, positions: list[dict]) -> float:
        return sum(self.calc_unrealized(p) for p in positions)

    # ─── 요약 ─────────────────────────────────────────────────────

    def get_summary(self, positions: list[dict]) -> dict:
        realized_total = self.get_realized_total()
        daily_realized = self.get_daily_realized()
        unrealized = self.get_unrealized_total(positions)
        trade_count = self.get_trade_count()

        return {
            "realized_total": round(realized_total, 4),
            "daily_realized": round(daily_realized, 4),
            "unrealized": round(unrealized, 4),
            "total_pnl": round(realized_total + unrealized, 4),
            "trade_count": trade_count,
            "positions": [
                {
                    "market": p.get("market"),
                    "symbol": p.get("symbol"),
                    "side": p.get("side"),
                    "qty": p.get("qty"),
                    "avg_price": p.get("avg_price"),
                    "mark_price": p.get("mark_price", p.get("avg_price")),
                    "leverage": p.get("leverage", 1),
                    "unrealized_pnl": round(self.calc_unrealized(p), 4),
                }
                for p in positions
            ],
        }

    def reset_daily(self) -> None:
        """일일 손익 초기화 (자정 실행용)."""
        self._redis.delete(_daily_key())
        logger.info("pnl_daily_reset")
