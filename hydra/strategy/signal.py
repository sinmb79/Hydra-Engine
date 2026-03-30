# hydra/strategy/signal.py
import time
from dataclasses import dataclass

_EMA_FAST = "EMA_9"
_EMA_SLOW = "EMA_20"
_RSI = "RSI_14"

_RSI_OVERSOLD = 30.0
_RSI_OVERBOUGHT = 70.0
_TREND_UP_RSI_LOW = 45.0
_TREND_UP_RSI_HIGH = 75.0
_TREND_DOWN_RSI_LOW = 25.0
_TREND_DOWN_RSI_HIGH = 55.0


@dataclass
class Signal:
    signal: str    # "BUY" | "SELL" | "HOLD"
    reason: str
    price: float
    ts: int


class SignalGenerator:
    def generate(self, indicators: dict, regime: str, close: float) -> Signal:
        ema9 = indicators.get(_EMA_FAST)
        ema20 = indicators.get(_EMA_SLOW)
        rsi = indicators.get(_RSI)
        ts = int(time.time() * 1000)

        if regime == "volatile":
            return Signal(signal="HOLD", reason="volatile: skip", price=close, ts=ts)

        if regime == "trending_up":
            if ema9 is not None and ema20 is not None and ema9 > ema20:
                if rsi is not None and _TREND_UP_RSI_LOW < rsi < _TREND_UP_RSI_HIGH:
                    return Signal(signal="BUY", reason="trend_up: ema_cross+rsi",
                                  price=close, ts=ts)
            return Signal(signal="HOLD", reason="trend_up: no_entry", price=close, ts=ts)

        if regime == "trending_down":
            if ema9 is not None and ema20 is not None and ema9 < ema20:
                if rsi is not None and _TREND_DOWN_RSI_LOW < rsi < _TREND_DOWN_RSI_HIGH:
                    return Signal(signal="SELL", reason="trend_down: ema_cross+rsi",
                                  price=close, ts=ts)
            return Signal(signal="HOLD", reason="trend_down: no_entry", price=close, ts=ts)

        # ranging (default)
        if rsi is not None:
            if rsi < _RSI_OVERSOLD:
                return Signal(signal="BUY", reason="ranging: rsi_oversold",
                              price=close, ts=ts)
            if rsi > _RSI_OVERBOUGHT:
                return Signal(signal="SELL", reason="ranging: rsi_overbought",
                              price=close, ts=ts)
        return Signal(signal="HOLD", reason="ranging: neutral", price=close, ts=ts)
