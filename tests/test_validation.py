import pytest
from hydra.config.validation import StrategyConfig, RiskConfig


def test_stop_loss_too_high():
    with pytest.raises(ValueError, match="너무 큽니다"):
        StrategyConfig(stop_loss_pct=0.99)


def test_stop_loss_zero():
    with pytest.raises(ValueError):
        StrategyConfig(stop_loss_pct=0.0)


def test_stop_loss_valid():
    cfg = StrategyConfig(stop_loss_pct=0.05)
    assert cfg.stop_loss_pct == 0.05


def test_position_size_too_high():
    with pytest.raises(ValueError, match="너무 큽니다"):
        StrategyConfig(position_size_pct=0.99)


def test_position_size_valid():
    cfg = StrategyConfig(position_size_pct=0.10)
    assert cfg.position_size_pct == 0.10


def test_risk_config_defaults():
    cfg = RiskConfig()
    assert cfg.daily_loss_limit_pct == 0.03
    assert cfg.daily_loss_kill_pct == 0.05
