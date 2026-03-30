# tests/test_supplemental_events.py
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hydra.supplemental.events import EventCalendarPoller


@pytest.mark.asyncio
async def test_fetch_returns_empty_without_api_key():
    r = MagicMock()
    poller = EventCalendarPoller(redis_client=r, api_key="")
    result = await poller._fetch()
    assert result == []


@pytest.mark.asyncio
async def test_fetch_parses_response():
    r = MagicMock()
    poller = EventCalendarPoller(redis_client=r, api_key="test_key")
    mock_response = {
        "body": [
            {
                "title": "Bitcoin Halving",
                "coins": [{"symbol": "BTC"}],
                "date_event": "2024-04-20T00:00:00Z",
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response
    mock_resp.raise_for_status = MagicMock()
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await poller._fetch()
    assert len(result) == 1
    assert result[0]["title"] == "Bitcoin Halving"
    assert result[0]["symbol"] == "BTC"
    assert result[0]["source"] == "coinmarketcal"


@pytest.mark.asyncio
async def test_run_writes_redis():
    r = MagicMock()
    r.set = AsyncMock()
    poller = EventCalendarPoller(redis_client=r, api_key="")
    with patch("hydra.supplemental.events.asyncio.sleep",
               side_effect=asyncio.CancelledError):
        try:
            await poller.run()
        except asyncio.CancelledError:
            pass
    r.set.assert_called_once()
    key, value = r.set.call_args[0]
    assert key == "hydra:events:upcoming"
    assert json.loads(value) == []
