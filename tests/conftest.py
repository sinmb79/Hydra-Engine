import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.set.return_value = True
    r.get.return_value = None
    r.delete.return_value = True
    return r


@pytest.fixture
def mock_exchange():
    ex = AsyncMock()
    ex.cancel_all.return_value = []
    ex.get_positions.return_value = []
    ex.cancel_order.return_value = {"status": "canceled"}
    return ex
