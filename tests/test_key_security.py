import os
import pytest
from pathlib import Path
from hydra.config.keys import KeyManager


def test_gitignore_contains_env():
    content = Path(".gitignore").read_text()
    assert ".env" in content
    assert "config/keys/" in content
    assert "*.key" in content


def test_key_roundtrip(tmp_path):
    km = KeyManager(master_key_path=str(tmp_path / "master.key"))
    km.store("binance", "my_api_key", "my_secret")
    api_key, secret = km.load("binance")
    assert api_key == "my_api_key"
    assert secret == "my_secret"


def test_stored_file_is_not_plaintext(tmp_path):
    km = KeyManager(master_key_path=str(tmp_path / "master.key"))
    km.store("upbit", "plain_key", "plain_secret")
    key_file = tmp_path / "upbit.enc"
    assert key_file.exists()
    raw = key_file.read_bytes()
    assert b"plain_key" not in raw
    assert b"plain_secret" not in raw


def test_withdrawal_check_no_permission(tmp_path):
    km = KeyManager(master_key_path=str(tmp_path / "master.key"))
    assert km.check_withdrawal_permission("binance") is False
