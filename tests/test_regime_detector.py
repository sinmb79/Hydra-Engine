# tests/test_regime_detector.py
from hydra.regime.detector import RegimeDetector

def test_volatile_regime():
    det = RegimeDetector()
    indicators = {"BBB_5_2.0_2.0": 0.10, "ADX_14": 30.0, "EMA_50": 45000.0}
    assert det.detect(indicators, close=50000.0) == "volatile"

def test_trending_up():
    det = RegimeDetector()
    indicators = {"BBB_5_2.0_2.0": 0.02, "ADX_14": 30.0, "EMA_50": 45000.0}
    assert det.detect(indicators, close=50000.0) == "trending_up"

def test_trending_down():
    det = RegimeDetector()
    indicators = {"BBB_5_2.0_2.0": 0.02, "ADX_14": 30.0, "EMA_50": 55000.0}
    assert det.detect(indicators, close=50000.0) == "trending_down"

def test_ranging():
    det = RegimeDetector()
    indicators = {"BBB_5_2.0_2.0": 0.02, "ADX_14": 15.0, "EMA_50": 45000.0}
    assert det.detect(indicators, close=50000.0) == "ranging"

def test_none_indicators_return_ranging():
    det = RegimeDetector()
    indicators = {"BBB_5_2.0_2.0": None, "ADX_14": None, "EMA_50": None}
    assert det.detect(indicators, close=50000.0) == "ranging"
