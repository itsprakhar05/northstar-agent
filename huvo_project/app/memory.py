import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR
from app.schemas import Channel


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def history(self, session_id: str) -> list[dict[str, Any]]:
        return list(self._session(session_id)["messages"])

    def channel(self, session_id: str) -> Channel:
        return self._session(session_id)["channel"]

    def set_channel(self, session_id: str, channel: Channel) -> None:
        self._session(session_id)["channel"] = channel

    def append(self, session_id: str, message: dict[str, Any]) -> None:
        self._session(session_id)["messages"].append(message)

    def mark_ended(self, session_id: str) -> None:
        self._session(session_id)["ended"] = True

    def is_ended(self, session_id: str) -> bool:
        return bool(self._session(session_id)["ended"])

    def add_response(self, session_id: str, response_data: dict[str, Any]) -> None:
        """Capture and store information from a user message."""
        if "responses" not in self._session(session_id):
            self._session(session_id)["responses"] = []
        self._session(session_id)["responses"].append(response_data)
        self.save_session(session_id)

    def set_analytics(self, session_id: str, analytics: dict[str, Any]) -> None:
        """Store analytics for the session."""
        self._session(session_id)["analytics"] = analytics
        self.save_session(session_id)

    def save_session(self, session_id: str) -> None:
        """Save session data to JSON file."""
        session = self._session(session_id)
        file_path = DATA_DIR / f"{session_id}.json"
        
        # Prepare data for JSON serialization
        data = {
            "session_id": session_id,
            "messages": session.get("messages", []),
            "channel": session.get("channel", "chat"),
            "ended": session.get("ended", False),
            "responses": session.get("responses", []),
            "analytics": session.get("analytics"),
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def reopen_session(self, session_id: str) -> None:
        """Reopen a closed session for continued conversation or updates."""
        self._session(session_id)["ended"] = False

    def load_session_from_file(self, session_id: str) -> dict[str, Any] | None:
        """Load saved session data from JSON file."""
        file_path = DATA_DIR / f"{session_id}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def get_session_data(self, session_id: str) -> dict[str, Any]:
        """Get current session data (both in-memory and from file)."""
        session = self._session(session_id)
        return {
            "session_id": session_id,
            "messages": session.get("messages", []),
            "channel": session.get("channel", "chat"),
            "ended": session.get("ended", False),
            "responses": session.get("responses", []),
            "analytics": session.get("analytics"),
        }

    def _session(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "messages": [],
                "channel": "chat",
                "ended": False,
                "responses": [],
                "analytics": None,
            }
        return self._sessions[session_id]


store = SessionStore()
