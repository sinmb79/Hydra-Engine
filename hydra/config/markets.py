from pathlib import Path
from typing import Optional

import yaml

from hydra.logging.setup import get_logger

logger = get_logger(__name__)

VALID_MARKETS = {"kr", "us", "upbit", "binance", "hl", "poly"}


class MarketManager:
    def __init__(self, config_path: str = "config/markets.yaml"):
        self._path = Path(config_path)
        self._data: dict = self._load()

    def _load(self) -> dict:
        if not self._path.exists():
            return {"markets": {m: {"enabled": False, "mode": "paper"} for m in VALID_MARKETS}}
        with self._path.open() as f:
            return yaml.safe_load(f) or {"markets": {}}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as f:
            yaml.dump(self._data, f, allow_unicode=True)

    def get_active_markets(self) -> list[str]:
        return [k for k, v in self._data.get("markets", {}).items() if v.get("enabled")]

    def is_active(self, market_id: str) -> bool:
        return self._data.get("markets", {}).get(market_id, {}).get("enabled", False)

    def enable(self, market_id: str, mode: str = "paper") -> None:
        if market_id not in VALID_MARKETS:
            raise ValueError(f"Unknown market '{market_id}'. Valid: {VALID_MARKETS}")
        markets = self._data.setdefault("markets", {})
        markets.setdefault(market_id, {})["enabled"] = True
        markets[market_id]["mode"] = mode
        self._save()
        logger.info("market_enabled", market=market_id, mode=mode)

    def disable(self, market_id: str) -> None:
        markets = self._data.get("markets", {})
        if market_id in markets:
            markets[market_id]["enabled"] = False
            self._save()
            logger.info("market_disabled", market=market_id)

    def get_mode(self, market_id: str) -> str:
        return self._data.get("markets", {}).get(market_id, {}).get("mode", "paper")
