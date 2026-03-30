import math
import pytest
from hydra.data.models import Candle
from hydra.indicator.calculator import IndicatorCalculator


def _make_candles(n: int) -> list[Candle]:
    candles = []
    price = 50000.0
    for i in range(n):
        open_ = price
        high = price * 1.001
        low = price * 0.999
        close = price * (1 + (0.001 if i % 2 == 0 else -0.001))
        price = close
        candles.append(Candle(
            market="binance", symbol="BTC/USDT", timeframe="1m",
            open_time=1_000_000 + i * 60_000,
            open=open_, high=high, low=low, close=close,
            volume=100.0 + i,
            close_time=1_000_000 + i * 60_000 + 59_999,
        ))
    return candles


def test_compute_returns_dict_with_rsi():
    calc = IndicatorCalculator()
    candles = _make_candles(250)
    result = calc.compute(candles)
    assert isinstance(result, dict)
    assert "RSI_14" in result
    assert isinstance(result["RSI_14"], float), "RSI_14 must be a valid float with 250 candles"


def test_compute_no_nan_values():
    calc = IndicatorCalculator()
    candles = _make_candles(250)
    result = calc.compute(candles)
    for key, val in result.items():
        if val is not None:
            assert not (isinstance(val, float) and math.isnan(val)), \
                f"NaN found for key {key}"


def test_compute_returns_empty_for_insufficient_candles():
    calc = IndicatorCalculator()
    candles = _make_candles(100)  # fewer than 210
    result = calc.compute(candles)
    assert result == {}


def test_compute_includes_calculated_at():
    calc = IndicatorCalculator()
    candles = _make_candles(250)
    result = calc.compute(candles)
    assert "calculated_at" in result
    assert isinstance(result["calculated_at"], int)
