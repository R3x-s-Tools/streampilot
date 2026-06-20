from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass, field
from queue import Queue
from typing import Callable, Optional


@dataclass
class ChatMessage:
    username: str
    message: str
    timestamp: float = field(default_factory=time.time)


class TwitchChatService:
    def __init__(self, nick: str, channel: str, oauth_provider: Callable[[], Optional[str]]):
        self.nick = nick.strip()
        self.channel = channel.lower().strip().lstrip("#")
        self.oauth_provider = oauth_provider
        self.sock = None
        self.running = False
        self.messages: Queue[ChatMessage] = Queue()
        self.status = "Stopped"
        self.last_error = ""

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass

    def drain(self) -> list[ChatMessage]:
        out = []
        while not self.messages.empty():
            out.append(self.messages.get())
        return out

    def _run(self):
        while self.running:
            try:
                oauth = self.oauth_provider()
                if not oauth:
                    raise RuntimeError("No OAuth token available. Login with Twitch first.")
                if not oauth.startswith("oauth:"):
                    oauth = f"oauth:{oauth}"

                self.status = "Connecting..."
                self.sock = socket.socket()
                self.sock.settimeout(20)
                self.sock.connect(("irc.chat.twitch.tv", 6667))
                self._send(f"PASS {oauth}")
                self._send(f"NICK {self.nick}")
                self._send("CAP REQ :twitch.tv/tags twitch.tv/commands")
                self._send(f"JOIN #{self.channel}")
                self.status = f"Connected to #{self.channel}"

                buffer = ""
                while self.running:
                    try:
                        data = self.sock.recv(4096).decode("utf-8", errors="ignore")
                    except socket.timeout:
                        continue
                    if not data:
                        raise ConnectionError("Twitch IRC returned empty data")
                    buffer += data
                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                        if line.startswith("PING"):
                            self._send("PONG :tmi.twitch.tv")
                        elif "Login authentication failed" in line:
                            raise PermissionError("Twitch chat authentication failed.")
                        elif " PRIVMSG " in line:
                            msg = self._parse_privmsg(line)
                            if msg:
                                self.messages.put(msg)
            except Exception as exc:
                self.last_error = str(exc)
                self.status = f"Error: {exc}"
                print(f"[TwitchChat ERROR] {exc}")
                time.sleep(5)

    def _send(self, command: str):
        self.sock.send(f"{command}\r\n".encode("utf-8"))

    def _parse_privmsg(self, line: str) -> ChatMessage | None:
        try:
            prefix, text = line.split(" PRIVMSG ", 1)
            message = text.split(" :", 1)[1]
            if " :" in prefix:
                prefix = prefix.split(" :", 1)[1]
            else:
                prefix = prefix.lstrip(":")
            username = prefix.split("!", 1)[0]
            return ChatMessage(username=username, message=message)
        except Exception:
            return None
