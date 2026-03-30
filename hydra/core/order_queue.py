import json
from dataclasses import dataclass
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from hydra.logging.setup import get_logger

logger = get_logger(__name__)

LOCK_TIMEOUT = 10
IDEMPOTENCY_TTL = 86400  # 24 hours
KILL_BLOCKED_KEY = "hydra:kill_switch_active"

FUTURES_MARKETS = {"binance", "hl"}  # 선물 거래를 지원하는 시장


class OrderLockError(Exception):
    pass


class OrderRequest(BaseModel):
    market: Literal["kr", "us", "upbit", "binance", "hl", "poly"]
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"] = "market"
    qty: Optional[float] = None
    price: Optional[float] = None
    amount: Optional[float] = None
    idempotency_key: str = ""
    exchange: Optional[str] = None
    leverage: int = Field(default=1, ge=1, le=125, description="선물 레버리지 (1~125x, 현물은 1로 고정)")
    is_futures: bool = Field(default=False, description="선물 주문 여부")

    def model_post_init(self, __context) -> None:
        if not self.idempotency_key:
            self.idempotency_key = str(uuid4())
        # 선물 지원 시장인데 leverage > 1이면 자동으로 is_futures=True
        if self.leverage > 1 and self.market in FUTURES_MARKETS:
            object.__setattr__(self, "is_futures", True)

    @field_validator("qty")
    @classmethod
    def validate_qty(cls, v):
        if v is not None and v <= 0:
            raise ValueError("수량은 양수여야 합니다")
        return v

    @field_validator("leverage")
    @classmethod
    def validate_leverage(cls, v):
        if v < 1 or v > 125:
            raise ValueError("레버리지는 1~125 사이여야 합니다")
        return v


@dataclass
class OrderResult:
    order_id: str
    status: str
    symbol: str
    market: str


class OrderQueue:
    def __init__(self, redis_client, risk_engine, position_tracker, exchanges: dict):
        self._redis = redis_client
        self._risk = risk_engine
        self._positions = position_tracker
        self._exchanges = exchanges
        self._blocked = False

    def block_new_orders(self) -> None:
        self._blocked = True

    async def submit(self, order: OrderRequest) -> OrderResult:
        # 멱등성 체크 (Kill Switch보다 먼저 — 캐시된 결과는 항상 반환)
        cached_raw = self._redis.get(f"idem:{order.idempotency_key}")
        if cached_raw:
            cached = json.loads(cached_raw)
            return OrderResult(
                order_id=cached["order_id"],
                status=cached["status"],
                symbol=order.symbol,
                market=order.market,
            )

        # Kill Switch 체크
        if self._blocked or self._redis.get(KILL_BLOCKED_KEY):
            raise OrderLockError("Kill Switch 활성 — 신규 주문 불가")

        # Redis 락 획득
        lock_key = f"order_lock:{order.market}:{order.symbol}:{order.side}"
        acquired = self._redis.set(lock_key, "1", nx=True, ex=LOCK_TIMEOUT)
        if not acquired:
            raise OrderLockError(f"주문 락 획득 실패: {order.symbol} {order.side}")

        try:
            # 리스크 검증
            allowed, reason = self._risk.check_order_allowed(order.market, order.symbol, 0.0)
            if not allowed:
                raise OrderLockError(f"리스크 검증 실패: {reason}")

            # 거래소 주문
            ex = self._exchanges.get(order.market)
            if not ex:
                raise OrderLockError(f"비활성 시장: {order.market}")

            # 선물 레버리지 설정 (주문 전)
            if order.is_futures and order.leverage > 1:
                await ex.set_leverage(order.symbol, order.leverage)

            raw = await ex.create_order(
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                qty=order.qty,
                price=order.price,
            )
            result = OrderResult(
                order_id=raw.get("order_id", str(uuid4())),
                status=raw.get("status", "submitted"),
                symbol=order.symbol,
                market=order.market,
            )

            # 멱등성 캐시 저장
            self._redis.set(
                f"idem:{order.idempotency_key}",
                json.dumps({"order_id": result.order_id, "status": result.status}),
                ex=IDEMPOTENCY_TTL,
            )
            logger.info("order_submitted", order_id=result.order_id, symbol=order.symbol, side=order.side, leverage=order.leverage)
            return result
        finally:
            self._redis.delete(lock_key)
