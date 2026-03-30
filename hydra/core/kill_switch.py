import time
from dataclasses import dataclass, field

from hydra.logging.setup import get_logger

logger = get_logger(__name__)

KILL_BLOCKED_KEY = "hydra:kill_switch_active"
DAILY_PNL_KEY = "hydra:daily_pnl"
KILL_THRESHOLD = -0.05


@dataclass
class KillSwitchResult:
    success: bool
    source: str
    reason: str
    duration_ms: float
    closed_positions: list = field(default_factory=list)
    errors: list = field(default_factory=list)


class KillSwitch:
    def __init__(self, exchanges: dict, position_tracker, telegram, redis_client):
        self._exchanges = exchanges
        self._positions = position_tracker
        self._telegram = telegram
        self._redis = redis_client

    async def execute(self, reason: str, source: str) -> KillSwitchResult:
        t0 = time.monotonic()
        logger.warning("kill_switch_triggered", reason=reason, source=source)

        # 1. 신규 주문 차단
        self._redis.set(KILL_BLOCKED_KEY, "1")

        # 2. 전 거래소 미체결 취소
        errors = []
        for name, ex in self._exchanges.items():
            try:
                await ex.cancel_all()
            except Exception as e:
                errors.append(f"{name}: cancel_all failed: {e}")
                logger.error("kill_switch_cancel_error", exchange=name, error=str(e))

        # 3. 전 포지션 시장가 청산
        positions = self._positions.get_all()
        closed = []
        for pos in positions:
            market = pos["market"]
            ex = self._exchanges.get(market)
            if ex:
                try:
                    close_side = "sell" if pos["side"] == "buy" else "buy"
                    await ex.create_order(
                        symbol=pos["symbol"],
                        side=close_side,
                        order_type="market",
                        qty=pos["qty"],
                    )
                    closed.append(pos["symbol"])
                except Exception as e:
                    errors.append(f"close {pos['symbol']}: {e}")

        duration_ms = (time.monotonic() - t0) * 1000

        # 4. Telegram 알림
        msg = f"🚨 Kill Switch 발동\n원인: {reason}\n경로: {source}\n청산: {len(closed)}개\n소요: {duration_ms:.0f}ms"
        try:
            await self._telegram.send_message(msg)
        except Exception as e:
            logger.error("kill_switch_telegram_error", error=str(e))

        logger.warning("kill_switch_complete", closed=len(closed), errors=len(errors), duration_ms=duration_ms)
        return KillSwitchResult(
            success=len(errors) == 0,
            source=source,
            reason=reason,
            duration_ms=duration_ms,
            closed_positions=closed,
            errors=errors,
        )

    async def check_auto_triggers(self) -> tuple[bool, str]:
        raw = self._redis.get(DAILY_PNL_KEY)
        daily_pnl = float(raw) if raw else 0.0
        if daily_pnl <= KILL_THRESHOLD:
            return True, f"daily_loss:{daily_pnl*100:.1f}%"
        return False, ""

    def is_active(self) -> bool:
        return bool(self._redis.get(KILL_BLOCKED_KEY))
