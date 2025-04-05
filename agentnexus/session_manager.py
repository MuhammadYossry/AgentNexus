from typing import Optional, Dict, Any
import json
import os
import uuid
from datetime import datetime
import redis
from loguru import logger

class SessionManager:
    """
    Redis-based session manager for workflow state persistence.
    Uses environment variables for configuration:
    - REDIS_HOST: Redis server hostname (default: localhost)
    - REDIS_PORT: Redis server port (default: 6379)
    - REDIS_DB: Redis database number (default: 0)
    - REDIS_PASSWORD: Redis password (default: None)
    - SESSION_TTL: Session time-to-live in seconds (default: 3600, 1 hour)
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        try:
            # Read configuration from environment variables with defaults
            redis_host = os.environ.get("REDIS_HOST", "localhost")
            redis_port = int(os.environ.get("REDIS_PORT", 6379))
            redis_db = int(os.environ.get("REDIS_DB", 0))
            redis_password = os.environ.get("REDIS_PASSWORD", None)
            self.session_ttl = int(os.environ.get("SESSION_TTL", 3600))  # 1 hour default
            # Initialize Redis client
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True  # Automatically decode responses to strings
            )
            # Test connection
            self.redis.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}/{redis_db}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            logger.warning("Falling back to in-memory session storage (not suitable for production)")
            self.redis = None
            self.in_memory_sessions = {}

    def _generate_session_key(self, session_id: str) -> str:
        """Generate a Redis key for the session."""
        return f"session:{session_id}"

    def create_session(self) -> str:
        """
        Create a new session and return its ID.
        Returns:
            str: The newly created session ID
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.now().isoformat(),
            "context": {}
        }
        if self.redis:
            # Store in Redis
            session_key = self._generate_session_key(session_id)
            self.redis.set(
                session_key,
                json.dumps(session_data),
                ex=self.session_ttl
            )
            logger.debug(f"Created new Redis session: {session_id}")
        else:
            # In-memory fallback
            self.in_memory_sessions[session_id] = session_data
            logger.debug(f"Created new in-memory session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by ID.
        Args:
            session_id (str): The session ID to retrieve
        Returns:
            Optional[Dict[str, Any]]: The session data if found, None otherwise
        """
        if self.redis:
            # Get from Redis
            session_key = self._generate_session_key(session_id)
            session_data = self.redis.get(session_key)
            if not session_data:
                logger.warning(f"Session not found: {session_id}")
                return None
            # Reset TTL on access
            self.redis.expire(session_key, self.session_ttl)
            try:
                return json.loads(session_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding session data: {str(e)}")
                return None
        else:
            # In-memory fallback
            return self.in_memory_sessions.get(session_id)

    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Update an existing session.
        Args:
            session_id (str): The session ID to update
            session_data (Dict[str, Any]): The new session data
        Returns:
            bool: True if successful, False otherwise
        """
        if self.redis:
            session_key = self._generate_session_key(session_id)
            # Check if session exists
            if not self.redis.exists(session_key):
                logger.warning(f"Cannot update non-existent session: {session_id}")
                return False
            # Update existing session
            try:
                # Get the existing session to merge the contexts
                existing_data = json.loads(self.redis.get(session_key))
                # Update context by merging
                # Properly merge nested context if it exists
                if "context" in session_data and "context" in existing_data:
                    existing_data["context"].update(session_data["context"])
                    # Create a new dict without the context key to avoid double-updating
                    session_data_without_context = {k: v for k, v in session_data.items() if k != "context"}
                    # Update the rest of the session data
                    existing_data.update(session_data_without_context)
                else:
                    # Regular update for other session data
                    existing_data.update(session_data)
                # Save updated session
                self.redis.set(
                    session_key,
                    json.dumps(existing_data),
                    ex=self.session_ttl
                )
                logger.debug(f"Updated session: {session_id}")
                return True
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Error updating session: {str(e)}")
                return False
        else:
            # In-memory fallback
            if session_id not in self.in_memory_sessions:
                logger.warning(f"Cannot update non-existent session: {session_id}")
                return False
            # Update existing session
            if "context" in session_data and "context" in self.in_memory_sessions[session_id]:
                self.in_memory_sessions[session_id]["context"].update(session_data["context"])
                session_data_without_context = {k: v for k, v in session_data.items() if k != "context"}
                self.in_memory_sessions[session_id].update(session_data_without_context)
            else:
                self.in_memory_sessions[session_id].update(session_data)
            logger.debug(f"Updated in-memory session: {session_id}")
            return True

    def close_session(self, session_id: str) -> bool:
        """
        Close and remove a session.
        Args:
            session_id (str): The session ID to close
        Returns:
            bool: True if successful, False otherwise
        """
        if self.redis:
            session_key = self._generate_session_key(session_id)
            result = self.redis.delete(session_key)
            success = result > 0
            if success:
                logger.debug(f"Closed session: {session_id}")
            else:
                logger.warning(f"Failed to close non-existent session: {session_id}")
            return success
        else:
            # In-memory fallback
            if session_id in self.in_memory_sessions:
                del self.in_memory_sessions[session_id]
                logger.debug(f"Closed in-memory session: {session_id}")
                return True
            else:
                logger.warning(f"Failed to close non-existent in-memory session: {session_id}")
                return False

    def create_workflow_session(self, workflow_id: str, initial_context: Dict[str, Any] = None) -> str:
        """
        Create a new session specifically for a workflow.

        Args:
            workflow_id: The ID of the workflow
            initial_context: Optional initial context data

        Returns:
            str: The newly created session ID
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "current_step": None,
            "step_history": [],
            "context": initial_context or {},
            "last_updated": datetime.now().isoformat()
        }
        if self.redis:
            session_key = self._generate_session_key(session_id)
            self.redis.set(
                session_key,
                json.dumps(session_data),
                ex=self.session_ttl
            )
            logger.debug(f"Created new workflow session: {session_id} for workflow: {workflow_id}")
        else:
            self.in_memory_sessions[session_id] = session_data
            logger.debug(f"Created new in-memory workflow session: {session_id}")
        return session_id

    def update_workflow_session(
        self,
        session_id: str,
        current_step: str = None,
        context_updates: Dict[str, Any] = None,
        ui_state: Dict[str, Any] = None
    ) -> bool:
        """
        Update a workflow session with new state.
        
        Args:
            session_id: The session ID to update
            current_step: The current step ID if changed
            context_updates: Updates to the context data
            ui_state: Current UI component states
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                logger.warning(f"Session not found: {session_id}")
                return False
            if current_step and current_step != session_data.get("current_step"):
                session_data["current_step"] = current_step
                session_data["step_history"] = session_data.get("step_history", []) + [current_step]
            if context_updates:
                session_data["context"] = {
                    **session_data.get("context", {}),
                    **context_updates
                }
            if ui_state:
                session_data["ui_state"] = {
                    **session_data.get("ui_state", {}),
                    **ui_state
                }
            session_data["last_updated"] = datetime.now().isoformat()
            return self.update_session(session_id, session_data)
        except Exception as e:
            logger.error(f"Error updating workflow session: {str(e)}")
            return False

    def get_workflow_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the context data for a workflow session.

        Args:
            session_id: The session ID

        Returns:
            Optional[Dict[str, Any]]: The session context if found, None otherwise
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return None
        return session_data.get("context", {})

    def get_workflow_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the complete workflow state including context and UI state.

        Args:
            session_id: The session ID

        Returns:
            Optional[Dict[str, Any]]: The complete workflow state if found, None otherwise
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return None

        return {
            "workflow_id": session_data.get("workflow_id"),
            "current_step": session_data.get("current_step"),
            "step_history": session_data.get("step_history", []),
            "context": session_data.get("context", {}),
            "ui_state": session_data.get("ui_state", {}),
            "created_at": session_data.get("created_at"),
            "last_updated": session_data.get("last_updated")
        }

    def validate_session(self, session_id: str, workflow_id: str) -> bool:
        """
        Validate that a session exists and belongs to the specified workflow.

        Args:
            session_id: The session ID to validate
            workflow_id: The expected workflow ID

        Returns:
            bool: True if valid, False otherwise
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        return session_data.get("workflow_id") == workflow_id

# Create and export the session manager singleton instance
session_manager = SessionManager()