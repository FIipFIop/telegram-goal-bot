"""
User repository for database operations on users table.
Handles user creation, retrieval, and updates.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from database.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self):
        """Initialize user repository with Supabase client."""
        self.client = get_supabase()

    async def create_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        timezone: str = "UTC"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user in the database.

        Args:
            user_id: Telegram user ID
            username: Telegram username (optional)
            first_name: User's first name (optional)
            timezone: User's timezone (default: UTC)

        Returns:
            Dict containing created user data, or None if creation failed
        """
        try:
            data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "timezone": timezone,
                "is_active": True
            }

            response = self.client.table("users").insert(data).execute()

            if response.data:
                logger.info(f"Created user {user_id} ({username})")
                return response.data[0]
            else:
                logger.error(f"Failed to create user {user_id}")
                return None

        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return None

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by Telegram user ID.

        Args:
            user_id: Telegram user ID

        Returns:
            Dict containing user data, or None if not found
        """
        try:
            response = self.client.table("users").select("*").eq("user_id", user_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            return None

    async def get_or_create_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        timezone: str = "UTC"
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing user or create new one if doesn't exist.

        Args:
            user_id: Telegram user ID
            username: Telegram username (optional)
            first_name: User's first name (optional)
            timezone: User's timezone (default: UTC)

        Returns:
            Dict containing user data
        """
        user = await self.get_user(user_id)

        if user is None:
            user = await self.create_user(user_id, username, first_name, timezone)

        return user

    async def update_user(
        self,
        user_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update user information.

        Args:
            user_id: Telegram user ID
            updates: Dictionary of fields to update

        Returns:
            Dict containing updated user data, or None if update failed
        """
        try:
            response = self.client.table("users").update(updates).eq("user_id", user_id).execute()

            if response.data:
                logger.info(f"Updated user {user_id}")
                return response.data[0]
            else:
                logger.error(f"Failed to update user {user_id}")
                return None

        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return None

    async def update_timezone(self, user_id: int, timezone: str) -> bool:
        """
        Update user's timezone.

        Args:
            user_id: Telegram user ID
            timezone: New timezone string

        Returns:
            True if update successful, False otherwise
        """
        result = await self.update_user(user_id, {"timezone": timezone})
        return result is not None

    async def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user (soft delete).

        Args:
            user_id: Telegram user ID

        Returns:
            True if deactivation successful, False otherwise
        """
        result = await self.update_user(user_id, {"is_active": False})
        return result is not None

    async def get_all_active_users(self) -> List[Dict[str, Any]]:
        """
        Get all active users.

        Returns:
            List of active user dictionaries
        """
        try:
            response = self.client.table("users").select("*").eq("is_active", True).execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving active users: {e}")
            return []

    async def user_exists(self, user_id: int) -> bool:
        """
        Check if a user exists in the database.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user exists, False otherwise
        """
        user = await self.get_user(user_id)
        return user is not None
