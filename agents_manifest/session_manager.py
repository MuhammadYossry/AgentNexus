from typing import Optional, Dict, Any, Union
import json
import os
import uuid
from datetime import datetime, timedelta
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
    def __init__(self):
        """Initialize Redis connection using environment variables with defaults."""
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