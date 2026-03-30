import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hydra.resilience.graceful import GracefulManager


@pytest.mark.asyncio
async def test_shutdown_saves_state():
    order_queue = MagicMock()
    order_queue.block_new_orders = MagicMock()
    position_tracker = AsyncMock()
    position_tracker.snapshot.return_value = {"positions": []}
    redis_client = MagicMock()

    manager = GracefulManager(order_queue, position_tracker, redis_client)
    await manager.shutdown("SIGTERM")

    order_queue.block_new_orders.assert_called_once()
    position_tracker.snapshot.assert_called_once()
