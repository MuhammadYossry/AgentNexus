from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "context": {}
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    def update_session(self, session_id: str, context: Dict[str, Any]):
        if session_id in self.sessions:
            self.sessions[session_id]["context"].update(context)

    def close_session(self, session_id: str):
        self.sessions.pop(session_id, None)
