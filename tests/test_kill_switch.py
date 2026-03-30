import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from hydra.core.kill_switch import KillSwitch, KillSwitchResult

KILL_BLOCKED_KEY = "hydra:kill_switch_active"


@pytest.fixture
def ks(mock_redis, mock_exchange):
    telegram = AsyncMock()
    telegram.send_message = AsyncMock()
    positions = MagicMock()
    positions.get_all.return_value = [
        {"market": "kr", "symbol": "005930", "qty": 10, "side": "buy"}
    ]
    return KillSwitch(
        exchanges={"kr": mock_exchange},
        position_tracker=positions,
        telegram=telegram,
        redis_client=mock_redis,
    )


@pytest.mark.asyncio
async def test_kill_via_cli(ks, mock_exchange):
    result = await ks.execute(reason="test", source="cli")
    assert result.success
    mock_exchange.cancel_all.assert_called_once()


@pytest.mark.asyncio
async def test_kill_via_api(ks, mock_exchange):
    result = await ks.execute(reason="manual", source="api")
    assert result.success


@pytest.mark.asyncio
async def test_kill_blocks_new_orders(ks, mock_redis):
    await ks.execute(reason="test", source="cli")
    mock_redis.set.assert_any_call(KILL_BLOCKED_KEY, "1")


@pytest.mark.asyncio
async def test_kill_sends_telegram(ks):
    await ks.execute(reason="test", source="cli")
    ks._telegram.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_auto_trigger_daily_loss(ks, mock_redis):
    mock_redis.get.return_value = "-0.06"
    triggered, reason = await ks.check_auto_triggers()
    assert triggered
    assert "daily_loss" in reason


@pytest.mark.asyncio
async def test_auto_trigger_no_trigger(ks, mock_redis):
    mock_redis.get.return_value = "-0.01"
    triggered, _ = await ks.check_auto_triggers()
    assert not triggered
