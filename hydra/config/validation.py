from pydantic import BaseModel, field_validator


class StrategyConfig(BaseModel):
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05
    position_size_pct: float = 0.10
    max_positions: int = 5

    @field_validator("stop_loss_pct")
    @classmethod
    def validate_stop_loss(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("손절은 양수여야 합니다")
        if v > 0.20:
            raise ValueError(f"손절 {v * 100:.1f}%는 너무 큽니다 (최대 20%)")
        return v

    @field_validator("position_size_pct")
    @classmethod
    def validate_position_size(cls, v: float) -> float:
        if v > 0.50:
            raise ValueError(f"포지션 사이즈 {v * 100:.1f}%는 너무 큽니다 (최대 50%)")
        return v


class RiskConfig(BaseModel):
    daily_loss_limit_pct: float = 0.03
    daily_loss_kill_pct: float = 0.05
    max_position_per_symbol_pct: float = 0.20
    max_position_per_strategy_pct: float = 0.30
    max_position_per_market_pct: float = 0.50
    consecutive_loss_limit: int = 5
