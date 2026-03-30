import pytest
from unittest.mock import MagicMock, AsyncMock
from hydra.resilience.graceful import GracefulManager


@pytest.mark.asyncio
async def test_l1_graceful_shutdown_saves_state():
    """프로세스 종료 전 상태 저장 확인 (systemd Restart=always가 L1 보장)."""
    order_queue = MagicMock()
    order_queue.block_new_orders = MagicMock()
    position_tracker = AsyncMock()
    position_tracker.snapshot.return_value = {"positions": [{"symbol": "005930"}]}
    redis_client = MagicMock()

    manager = GracefulManager(order_queue, position_tracker, redis_client)
    await manager.shutdown("SIGTERM")

    order_queue.block_new_orders.assert_called_once()
    redis_client.set.assert_called_once()
    args = redis_client.set.call_args[0]
    assert "last_snapshot" in args[0]


def test_l2_watchdog_health_url_configurable():
    """Lambda 워치독 환경변수 설정 확인."""
    import importlib
    import os
    import sys

    os.environ["HYDRA_HEALTH_URL"] = "http://192.168.1.100:8000/health"

    # boto3/requests가 없을 경우 mock 처리
    mock_boto3 = MagicMock()
    mock_requests = MagicMock()
    sys.modules.setdefault("boto3", mock_boto3)
    sys.modules.setdefault("requests", mock_requests)

    import scripts.dr_watchdog as wd
    importlib.reload(wd)
    assert "192.168.1.100" in wd.HEALTH_URL
    del os.environ["HYDRA_HEALTH_URL"]
