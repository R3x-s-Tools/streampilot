import json
import stat
from pathlib import Path

import pytest

from core.secret_store import (
    FileSecretStore,
    KeyringSecretStore,
    MigratingSecretStore,
    SecretStoreError,
    create_twitch_secret_store,
)
from services.twitch_auth import TokenStore, TwitchAuthService


class InMemorySecretStore:
    def __init__(self) -> None:
        self.payload = None

    def load(self):
        return self.payload

    def save(self, payload):
        self.payload = payload

    def delete(self):
        self.payload = None


class FakeKeyring:
    def __init__(self, fail_writes: bool = False) -> None:
        self.value = None
        self.fail_writes = fail_writes

    def get_password(self, service_name, username):
        return self.value

    def set_password(self, service_name, username, password):
        if self.fail_writes:
            raise RuntimeError("keyring unavailable")
        self.value = password

    def delete_password(self, service_name, username):
        self.value = None


def test_twitch_auth_uses_injected_secret_store(tmp_path: Path) -> None:
    store = InMemorySecretStore()
    service = TwitchAuthService(
        client_id="cid",
        client_secret="secret",
        redirect_uri="http://localhost/callback",
        token_path=str(tmp_path / "tokens.json"),
        secret_store=store,
    )

    assert service._token is None
    assert service.secret_store is store

    service.save(
        TokenStore(
            access_token="abc",
            refresh_token="def",
            expires_at=0,
            scope=["chat:read"],
            token_type="bearer",
        )
    )

    assert store.payload is not None
    assert store.payload["access_token"] == "abc"


def test_file_secret_store_round_trip(tmp_path: Path) -> None:
    secret_path = tmp_path / "tokens.json"
    store = FileSecretStore(secret_path)

    store.save({"access_token": "abc"})

    assert store.load() == {"access_token": "abc"}
    assert stat.S_IMODE(secret_path.stat().st_mode) == 0o600


def test_file_secret_store_repairs_legacy_permissions_on_load(tmp_path: Path) -> None:
    secret_path = tmp_path / "tokens.json"
    secret_path.write_text('{"access_token": "abc"}', encoding="utf-8")
    secret_path.chmod(0o644)

    assert FileSecretStore(secret_path).load() == {"access_token": "abc"}
    assert stat.S_IMODE(secret_path.stat().st_mode) == 0o600


def test_existing_file_tokens_migrate_only_after_verified_keyring_write(
    tmp_path: Path,
) -> None:
    secret_path = tmp_path / "tokens.json"
    file_store = FileSecretStore(secret_path)
    payload = {"access_token": "abc", "refresh_token": "def"}
    file_store.save(payload)
    backend = FakeKeyring()
    keyring_store = KeyringSecretStore("StreamPilot.Twitch", "oauth_tokens", backend)

    store = MigratingSecretStore(primary=keyring_store, legacy=file_store)

    assert store.load() == payload
    assert json.loads(backend.value) == payload
    assert not secret_path.exists()


def test_failed_keyring_migration_preserves_existing_file(tmp_path: Path) -> None:
    secret_path = tmp_path / "tokens.json"
    file_store = FileSecretStore(secret_path)
    payload = {"access_token": "abc", "refresh_token": "def"}
    file_store.save(payload)
    keyring_store = KeyringSecretStore(
        "StreamPilot.Twitch",
        "oauth_tokens",
        FakeKeyring(fail_writes=True),
    )

    store = MigratingSecretStore(primary=keyring_store, legacy=file_store)

    with pytest.raises(SecretStoreError):
        store.load()
    assert file_store.load() == payload
    assert stat.S_IMODE(secret_path.stat().st_mode) == 0o600


def test_file_mode_remains_available_for_development(tmp_path: Path) -> None:
    store = create_twitch_secret_store(tmp_path / "tokens.json", mode="file")

    assert isinstance(store, FileSecretStore)


def test_default_store_uses_keyring_with_legacy_migration(tmp_path: Path) -> None:
    store = create_twitch_secret_store(
        tmp_path / "tokens.json",
        keyring_backend=FakeKeyring(),
    )

    assert isinstance(store, MigratingSecretStore)


def test_environment_selects_file_fallback_for_development(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STREAMPILOT_SECRET_STORE", "file")

    store = create_twitch_secret_store(tmp_path / "tokens.json")

    assert isinstance(store, FileSecretStore)
