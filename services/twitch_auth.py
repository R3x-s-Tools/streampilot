from __future__ import annotations

import json
import secrets
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

import requests

SCOPES = [
    "chat:read",
    "chat:edit",
    "moderator:read:followers",
    "channel:read:subscriptions",
    "bits:read",
    "channel:read:redemptions",
]


@dataclass
class TokenStore:
    access_token: str
    refresh_token: str
    expires_at: float
    scope: list[str]
    token_type: str = "bearer"


class TwitchAuthService:
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    AUTHORIZE_URL = "https://id.twitch.tv/oauth2/authorize"
    VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_path: str = "data/twitch_tokens.json",
    ):
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.redirect_uri = redirect_uri.strip()
        self.token_path = Path(token_path)
        self.token_path.parent.mkdir(exist_ok=True)
        self.status = "Not logged in"
        self.last_error = ""
        self._token: Optional[TokenStore] = None
        self.load()

    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    def load(self) -> Optional[TokenStore]:
        if not self.token_path.exists():
            return None
        try:
            data = json.loads(self.token_path.read_text(encoding="utf-8"))
            self._token = TokenStore(**data)
            self.status = "Token loaded"
            return self._token
        except Exception as exc:
            self.last_error = str(exc)
            self.status = f"Token load error: {exc}"
            return None

    def save(self, token: TokenStore) -> None:
        self._token = token
        self.token_path.write_text(json.dumps(asdict(token), indent=2), encoding="utf-8")

    def ensure_access_token(self) -> Optional[TokenStore]:
        if not self._token:
            self.load()
        if not self._token:
            self.status = "Not logged in"
            return None
        if time.time() >= self._token.expires_at - 300:
            return self.refresh()
        self.status = "Authenticated"
        return self._token

    def access_token(self) -> Optional[str]:
        token = self.ensure_access_token()
        return token.access_token if token else None

    def oauth_token(self) -> Optional[str]:
        token = self.ensure_access_token()
        return f"oauth:{token.access_token}" if token else None

    def refresh(self) -> Optional[TokenStore]:
        if not self._token:
            self.status = "No refresh token available"
            return None
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._token.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=15,
            )
            if response.status_code >= 400:
                self.last_error = f"Refresh failed {response.status_code}: {response.text[:500]}"
                self.status = self.last_error
                return None
            data = response.json()
            token = TokenStore(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", self._token.refresh_token),
                expires_at=time.time() + int(data.get("expires_in", 0)),
                scope=data.get("scope", []),
                token_type=data.get("token_type", "bearer"),
            )
            self.save(token)
            self.status = "Access token refreshed"
            self.last_error = ""
            return token
        except Exception as exc:
            self.last_error = str(exc)
            self.status = f"Refresh error: {exc}"
            return None

    def login_interactive(self, timeout_seconds: int = 180) -> bool:
        if not self.configured():
            self.status = "Missing Client ID, Client Secret, or Redirect URI"
            return False

        parsed = urllib.parse.urlparse(self.redirect_uri)
        host = parsed.hostname or "localhost"
        port = parsed.port or 17563
        callback_path = parsed.path or "/callback"
        state = secrets.token_urlsafe(24)
        result = {"code": None, "error": None}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                incoming = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(incoming.query)
                if incoming.path != callback_path:
                    self.send_response(404)
                    self.end_headers()
                    return
                if params.get("state", [""])[0] != state:
                    result["error"] = "State mismatch"
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"State mismatch. You can close this tab.")
                    return
                if "error" in params:
                    result["error"] = params.get(
                        "error_description", params.get("error", ["Unknown error"])
                    )[0]
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Twitch authorization failed. You can close this tab.")
                    return
                result["code"] = params.get("code", [None])[0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Dad_R3x Command Center is authorized. You can close this tab.")

            def log_message(self, fmt, *args):
                return

        server = HTTPServer((host, port), Handler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()

        query = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": " ".join(SCOPES),
                "state": state,
            }
        )
        webbrowser.open(f"{self.AUTHORIZE_URL}?{query}")
        self.status = "Waiting for Twitch login..."

        start = time.time()
        while time.time() - start < timeout_seconds:
            if result["code"] or result["error"]:
                break
            time.sleep(0.25)

        server.server_close()

        if result["error"]:
            self.status = f"Login failed: {result['error']}"
            self.last_error = result["error"]
            return False
        if not result["code"]:
            self.status = "Login timed out"
            self.last_error = "No authorization response received"
            return False
        return self._exchange_code(result["code"])

    def _exchange_code(self, code: str) -> bool:
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
                timeout=15,
            )
            if response.status_code >= 400:
                self.status = f"Code exchange failed {response.status_code}: {response.text[:500]}"
                self.last_error = self.status
                return False
            data = response.json()
            token = TokenStore(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_at=time.time() + int(data.get("expires_in", 0)),
                scope=data.get("scope", []),
                token_type=data.get("token_type", "bearer"),
            )
            self.save(token)
            self.status = "Logged in with Twitch"
            self.last_error = ""
            return True
        except Exception as exc:
            self.status = f"Code exchange error: {exc}"
            self.last_error = str(exc)
            return False

    def validate(self) -> dict | None:
        token = self.ensure_access_token()
        if not token:
            return None
        try:
            response = requests.get(
                self.VALIDATE_URL,
                headers={"Authorization": f"OAuth {token.access_token}"},
                timeout=10,
            )
            if response.status_code >= 400:
                self.last_error = f"Validate failed {response.status_code}: {response.text[:300]}"
                return None
            return response.json()
        except Exception as exc:
            self.last_error = str(exc)
            return None
