import json
import logging
from typing import Dict, Any, Optional
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

class RedisSessionManager:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis = None

    async def connect(self):
        if not self._redis:
            self._redis = await aioredis.from_url(
                self.redis_url, 
                encoding="utf-8", 
                decode_responses=True
            )
            logger.info("Connected to Redis successfully.")

    async def close(self):
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed.")

    async def get_session(self, user_id: str) -> Dict[str, Any]:
        """Retrieves session state from Redis. Returns a default initial session if not found."""
        await self.connect()
        key = f"bob_session:{user_id}"
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error fetching session from Redis: {e}")
        
        # Return default initial state if no session exists or error occurs
        return {
            "user_id": user_id,
            "current_flow": "main_menu",
            "current_step": "start",
            "context": {}
        }

    async def set_session(self, user_id: str, session_data: Dict[str, Any], expiry: int = 1800) -> None:
        """Sets session state with expiry in seconds (default 30 mins)"""
        await self.connect()
        key = f"bob_session:{user_id}"
        try:
            await self._redis.setex(key, expiry, json.dumps(session_data))
        except Exception as e:
            logger.error(f"Error saving session to Redis: {e}")

    async def update_session(self, user_id: str, flow: Optional[str] = None, step: Optional[str] = None, context_update: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Atomically updates flow, step, and context variables for a user."""
        session = await self.get_session(user_id)
        if flow is not None:
            session["current_flow"] = flow
        if step is not None:
            session["current_step"] = step
        if context_update is not None:
            session["context"].update(context_update)
        await self.set_session(user_id, session)
        return session

    async def clear_session(self, user_id: str) -> None:
        """Deletes session context to restart dialogue loop."""
        await self.connect()
        key = f"bob_session:{user_id}"
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Error clearing session in Redis: {e}")

# Global session manager instance
redis_manager = RedisSessionManager(settings.REDIS_URL)
