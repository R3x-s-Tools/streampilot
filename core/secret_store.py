from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Protocol


class SecretStoreError(RuntimeError):
    """Raised when a secret store cannot safely complete an operation."""


class SecretStore:
    """Persistence boundary for sensitive runtime data."""

    def load(self) -> dict[str, Any] | None:
        raise NotImplementedError

    def save(self, payload: dict[str, Any]) -> None:
        raise NotImplementedError

    def delete(self) -> None:
        raise NotImplementedError


class FileSecretStore(SecretStore):
    """Development fallback that stores secrets in a mode-0600 JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            self._restrict_path_permissions(self.path)
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save(self, payload: dict[str, Any]) -> None:
        serialized = json.dumps(payload, indent=2)
        temporary_path: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
            )
            temporary_path = Path(temporary_name)
            self._restrict_descriptor_permissions(descriptor)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            temporary_path.replace(self.path)
            self._restrict_path_permissions(self.path)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise SecretStoreError(f"Could not persist file-backed secret: {exc}") from exc

    def delete(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            raise SecretStoreError(f"Could not remove file-backed secret: {exc}") from exc

    @staticmethod
    def _restrict_descriptor_permissions(descriptor: int) -> None:
        if os.name != "nt":
            os.fchmod(descriptor, stat.S_IRUSR | stat.S_IWUSR)

    @staticmethod
    def _restrict_path_permissions(path: Path) -> None:
        if os.name != "nt":
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)


class KeyringBackend(Protocol):
    def get_password(self, service_name: str, username: str) -> str | None: ...

    def set_password(self, service_name: str, username: str, password: str) -> None: ...

    def delete_password(self, service_name: str, username: str) -> None: ...


class KeyringSecretStore(SecretStore):
    """Stores a JSON secret in the operating system credential manager."""

    def __init__(
        self,
        service_name: str,
        username: str,
        backend: KeyringBackend | None = None,
    ) -> None:
        if backend is None:
            try:
                import keyring
            except ImportError as exc:  # pragma: no cover - dependency/runtime guard
                raise SecretStoreError("The keyring package is unavailable") from exc
            if keyring.get_keyring().priority <= 0:
                raise SecretStoreError("No supported OS credential store is available")
            backend = keyring
        self.service_name = service_name
        self.username = username
        self.backend = backend

    def load(self) -> dict[str, Any] | None:
        try:
            serialized = self.backend.get_password(self.service_name, self.username)
        except Exception as exc:
            raise SecretStoreError(f"Could not read the OS credential store: {exc}") from exc
        if serialized is None:
            return None
        try:
            payload = json.loads(serialized)
        except json.JSONDecodeError as exc:
            raise SecretStoreError("OS credential store contained invalid JSON") from exc
        if not isinstance(payload, dict):
            raise SecretStoreError("OS credential store contained an invalid secret payload")
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        try:
            self.backend.set_password(
                self.service_name,
                self.username,
                json.dumps(payload),
            )
        except Exception as exc:
            raise SecretStoreError(f"Could not write to the OS credential store: {exc}") from exc

    def delete(self) -> None:
        try:
            self.backend.delete_password(self.service_name, self.username)
        except Exception as exc:
            # Keyring backends commonly raise when the entry is already absent.
            if self.load() is not None:
                raise SecretStoreError(f"Could not remove the OS credential: {exc}") from exc


class MigratingSecretStore(SecretStore):
    """Moves a legacy secret to a primary store without risking data loss."""

    def __init__(self, primary: SecretStore, legacy: SecretStore) -> None:
        self.primary = primary
        self.legacy = legacy

    def load(self) -> dict[str, Any] | None:
        primary_payload = self.primary.load()
        legacy_payload = self.legacy.load()
        if legacy_payload is None:
            return primary_payload
        if primary_payload == legacy_payload:
            self.legacy.delete()
            return primary_payload

        self.primary.save(legacy_payload)
        if self.primary.load() != legacy_payload:
            raise SecretStoreError("OS credential migration could not be verified")
        self.legacy.delete()
        return legacy_payload

    def save(self, payload: dict[str, Any]) -> None:
        self.primary.save(payload)

    def delete(self) -> None:
        self.primary.delete()
        self.legacy.delete()


def create_twitch_secret_store(
    token_path: str | Path,
    *,
    mode: str | None = None,
    keyring_backend: KeyringBackend | None = None,
) -> SecretStore:
    """Create the Twitch store, retaining an explicit file mode for development."""

    file_store = FileSecretStore(token_path)
    selected_mode = (mode or os.getenv("STREAMPILOT_SECRET_STORE", "keyring")).strip().lower()
    if selected_mode == "file":
        return file_store
    if selected_mode != "keyring":
        raise SecretStoreError("STREAMPILOT_SECRET_STORE must be 'keyring' or 'file'")
    primary = KeyringSecretStore(
        service_name="StreamPilot.Twitch",
        username="oauth_tokens",
        backend=keyring_backend,
    )
    return MigratingSecretStore(primary=primary, legacy=file_store)
