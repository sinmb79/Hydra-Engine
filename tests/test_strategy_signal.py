# tests/test_strategy_signal.py
from hydra.strategy.signal import SignalGenerator


def test_volatile_returns_hold():
    gen = SignalGenerator()
    indicators = {"EMA_9": 1.1, "EMA_20": 1.0, "RSI_14": 60.0}
    sig = gen.generate(indicators, "volatile", 50000.0)
    assert sig.signal == "HOLD"
    assert sig.reason == "volatile: skip"


def test_trending_up_buy():
    gen = SignalGenerator()
    indicators = {"EMA_9": 1.1, "EMA_20": 1.0, "RSI_14": 55.0}
    sig = gen.generate(indicators, "trending_up", 50000.0)
    assert sig.signal == "BUY"
    assert sig.reason == "trend_up: ema_cross+rsi"


def test_trending_up_hold_no_cross():
    gen = SignalGenerator()
    indicators = {"EMA_9": 0.9, "EMA_20": 1.0, "RSI_14": 55.0}
    sig = gen.generate(indicators, "trending_up", 50000.0)
    assert sig.signal == "HOLD"


def test_trending_down_sell():
    gen = SignalGenerator()
    indicators = {"EMA_9": 0.9, "EMA_20": 1.0, "RSI_14": 40.0}
    sig = gen.generate(indicators, "trending_down", 50000.0)
    assert sig.signal == "SELL"
    assert sig.reason == "trend_down: ema_cross+rsi"


def test_trending_down_hold_no_cross():
    gen = SignalGenerator()
    indicators = {"EMA_9": 1.1, "EMA_20": 1.0, "RSI_14": 40.0}
    sig = gen.generate(indicators, "trending_down", 50000.0)
    assert sig.signal == "HOLD"


def test_ranging_buy_oversold():
    gen = SignalGenerator()
    indicators = {"EMA_9": 1.0, "EMA_20": 1.0, "RSI_14": 25.0}
    sig = gen.generate(indicators, "ranging", 50000.0)
    assert sig.signal == "BUY"
    assert sig.reason == "ranging: rsi_oversold"


def test_ranging_sell_overbought():
    gen = SignalGenerator()
    indicators = {"EMA_9": 1.0, "EMA_20": 1.0, "RSI_14": 75.0}
    sig = gen.generate(indicators, "ranging", 50000.0)
    assert sig.signal == "SELL"
    assert sig.reason == "ranging: rsi_overbought"


def test_none_indicators_return_hold():
    gen = SignalGenerator()
    indicators = {"EMA_9": None, "EMA_20": None, "RSI_14": None}
    sig = gen.generate(indicators, "trending_up", 50000.0)
    assert sig.signal == "HOLD"
