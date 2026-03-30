import json
import os
from pathlib import Path

from cryptography.fernet import Fernet

from hydra.logging.setup import get_logger

logger = get_logger(__name__)


class KeyManager:
    def __init__(self, master_key_path: str = "~/.hydra/master.key"):
        self._master_path = Path(master_key_path).expanduser()
        self._key_dir = self._master_path.parent
        self._fernet = self._load_or_create_fernet()

    def _load_or_create_fernet(self) -> Fernet:
        self._key_dir.mkdir(parents=True, exist_ok=True)
        if self._master_path.exists():
            raw = self._master_path.read_bytes()
        else:
            raw = Fernet.generate_key()
            self._master_path.write_bytes(raw)
            self._master_path.chmod(0o600)
            logger.info("master_key_created", path=str(self._master_path))
        return Fernet(raw)

    def encrypt(self, plain: str) -> bytes:
        return self._fernet.encrypt(plain.encode())

    def decrypt(self, token: bytes) -> str:
        return self._fernet.decrypt(token).decode()

    def store(self, exchange: str, api_key: str, secret: str) -> None:
        payload = json.dumps({"api_key": api_key, "secret": secret})
        encrypted = self.encrypt(payload)
        out = self._key_dir / f"{exchange}.enc"
        out.write_bytes(encrypted)
        out.chmod(0o600)
        logger.info("key_stored", exchange=exchange)

    def load(self, exchange: str) -> tuple[str, str]:
        path = self._key_dir / f"{exchange}.enc"
        if not path.exists():
            raise FileNotFoundError(f"No stored key for exchange '{exchange}'")
        payload = json.loads(self.decrypt(path.read_bytes()))
        return payload["api_key"], payload["secret"]

    def check_withdrawal_permission(self, exchange: str) -> bool:
        """Placeholder — subclasses override for exchange-specific checks."""
        return False
