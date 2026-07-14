from pathlib import Path

from services.twitch_auth import TokenStore, TwitchAuthService
from core.secret_store import FileSecretStore


class InMemorySecretStore:
    def __init__(self) -> None:
        self.payload = None

    def load(self):
        return self.payload

    def save(self, payload):
        self.payload = payload


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
