import pytest
from unittest.mock import AsyncMock, MagicMock
from hydra.core.order_queue import OrderQueue, OrderRequest, OrderLockError


@pytest.fixture
def queue(mock_redis, mock_exchange):
    risk = MagicMock()
    risk.check_order_allowed.return_value = (True, "ok")
    positions = MagicMock()
    exchanges = {"kr": mock_exchange}
    mock_exchange.create_order = AsyncMock(return_value={"order_id": "ORD123", "status": "filled"})
    return OrderQueue(redis_client=mock_redis, risk_engine=risk, position_tracker=positions, exchanges=exchanges)


@pytest.mark.asyncio
async def test_order_submitted_successfully(queue, mock_redis):
    mock_redis.set.return_value = True  # lock acquired
    mock_redis.get.return_value = None  # no idempotency hit
    order = OrderRequest(market="kr", symbol="005930", side="buy", qty=10)
    result = await queue.submit(order)
    assert result.order_id is not None


@pytest.mark.asyncio
async def test_duplicate_lock_raises(queue, mock_redis):
    mock_redis.set.return_value = False  # lock already held
    mock_redis.get.return_value = None
    order = OrderRequest(market="kr", symbol="005930", side="buy", qty=10)
    with pytest.raises(OrderLockError):
        await queue.submit(order)


@pytest.mark.asyncio
async def test_idempotency_returns_cached(queue, mock_redis):
    import json
    cached = json.dumps({"order_id": "CACHED_ID", "status": "filled"})
    mock_redis.get.return_value = cached
    order = OrderRequest(market="kr", symbol="005930", side="buy", qty=10, idempotency_key="fixed-key")
    result = await queue.submit(order)
    assert result.order_id == "CACHED_ID"


@pytest.mark.asyncio
async def test_blocked_when_kill_switch_active(queue, mock_redis):
    mock_redis.get.side_effect = lambda k: "1" if "kill_switch" in k else None
    order = OrderRequest(market="kr", symbol="005930", side="buy", qty=10)
    with pytest.raises(OrderLockError, match="Kill Switch"):
        await queue.submit(order)
