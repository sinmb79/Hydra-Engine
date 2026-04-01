from hydra.config.settings import get_settings
from hydra.data.storage.base import Candle, OhlcvStore


def create_store() -> OhlcvStore:
    url = get_settings().db_url
    if url.startswith("sqlite"):
        # sqlite:///data/hydra.db → data/hydra.db
        path = url.split("///", 1)[-1]
        from hydra.data.storage.sqlite import SQLiteStore
        return SQLiteStore(path)
    elif url.startswith("postgresql") or url.startswith("postgres"):
        from hydra.data.storage.postgres import PostgresStore
        return PostgresStore(url)
    else:
        raise ValueError(f"Unsupported DB_URL scheme: {url}")


__all__ = ["create_store", "Candle", "OhlcvStore"]
