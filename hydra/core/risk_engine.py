from hydra.config.validation import RiskConfig
from hydra.core.position_tracker import PositionTracker
from hydra.logging.setup import get_logger

logger = get_logger(__name__)

DAILY_PNL_KEY = "hydra:daily_pnl"


class RiskEngine:
    def __init__(self, redis_client, position_tracker: PositionTracker, config: RiskConfig | None = None):
        self._redis = redis_client
        self._positions = position_tracker
        self._config = config or RiskConfig()

    def get_daily_pnl_pct(self) -> float:
        raw = self._redis.get(DAILY_PNL_KEY)
        return float(raw) if raw else 0.0

    def update_daily_pnl(self, pnl_pct: float) -> None:
        self._redis.set(DAILY_PNL_KEY, str(pnl_pct))

    def check_order_allowed(self, market: str, symbol: str, position_pct: float) -> tuple[bool, str]:
        """주문 허용 여부 확인. (allowed, reason) 반환."""
        daily_pnl = self.get_daily_pnl_pct()
        if daily_pnl <= -self._config.daily_loss_kill_pct:
            return False, f"일일 손실 {daily_pnl*100:.1f}% — Kill Switch 레벨"
        if daily_pnl <= -self._config.daily_loss_limit_pct:
            return False, f"일일 손실 {daily_pnl*100:.1f}% — 신규 주문 중단"
        if position_pct > self._config.max_position_per_symbol_pct:
            return False, f"종목 포지션 {position_pct*100:.1f}% 초과 (최대 {self._config.max_position_per_symbol_pct*100:.0f}%)"
        return True, "ok"

    def should_kill_switch(self) -> tuple[bool, str]:
        daily_pnl = self.get_daily_pnl_pct()
        if daily_pnl <= -self._config.daily_loss_kill_pct:
            return True, f"daily_loss:{daily_pnl*100:.1f}%"
        return False, ""
