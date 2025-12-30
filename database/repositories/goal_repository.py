"""
Goal repository for database operations on goals table.
Handles goal creation, retrieval, updates, and deletion.
"""

from typing import Optional, List, Dict, Any
from datetime import date
from database.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


class GoalRepository:
    """Repository for goal-related database operations."""

    def __init__(self):
        """Initialize goal repository with Supabase client."""
        self.client = get_supabase()

    async def create_goal(
        self,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        target_date: Optional[date] = None,
        priority: int = 3,
        ai_clarifications: Optional[List[Dict[str, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new goal.

        Args:
            user_id: Telegram user ID
            title: Goal title
            description: Goal description
            category: Goal category (fitness, education, etc.)
            target_date: Target completion date
            priority: Priority (1-5)
            ai_clarifications: List of Q&A from AI clarification
            metadata: Additional metadata

        Returns:
            Dict containing created goal data, or None if failed
        """
        try:
            data = {
                "user_id": user_id,
                "title": title,
                "description": description,
                "category": category,
                "target_date": target_date.isoformat() if target_date else None,
                "priority": priority,
                "status": "active",
                "ai_clarifications": ai_clarifications or [],
                "metadata": metadata or {}
            }

            response = self.client.table("goals").insert(data).execute()

            if response.data:
                logger.info(f"Created goal '{title}' for user {user_id}")
                return response.data[0]
            else:
                logger.error(f"Failed to create goal '{title}'")
                return None

        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            return None

    async def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a goal by ID.

        Args:
            goal_id: Goal UUID

        Returns:
            Dict containing goal data, or None if not found
        """
        try:
            response = self.client.table("goals").select("*").eq("id", goal_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error retrieving goal {goal_id}: {e}")
            return None

    async def get_user_goals(
        self,
        user_id: int,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all goals for a user, optionally filtered by status.

        Args:
            user_id: Telegram user ID
            status: Optional status filter ('active', 'completed', 'paused', 'cancelled')

        Returns:
            List of goal dictionaries
        """
        try:
            query = self.client.table("goals").select("*").eq("user_id", user_id)

            if status:
                query = query.eq("status", status)

            query = query.order("created_at", desc=True)
            response = query.execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving goals for user {user_id}: {e}")
            return []

    async def update_goal(
        self,
        goal_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a goal.

        Args:
            goal_id: Goal UUID
            updates: Dictionary of fields to update

        Returns:
            Dict containing updated goal data, or None if failed
        """
        try:
            response = self.client.table("goals").update(updates).eq("id", goal_id).execute()

            if response.data:
                logger.info(f"Updated goal {goal_id}")
                return response.data[0]
            else:
                logger.error(f"Failed to update goal {goal_id}")
                return None

        except Exception as e:
            logger.error(f"Error updating goal {goal_id}: {e}")
            return None

    async def update_clarifications(
        self,
        goal_id: str,
        qa_history: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """
        Update AI clarification Q&A history for a goal.

        Args:
            goal_id: Goal UUID
            qa_history: List of question-answer pairs

        Returns:
            Updated goal data or None
        """
        return await self.update_goal(goal_id, {"ai_clarifications": qa_history})

    async def update_status(
        self,
        goal_id: str,
        status: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update goal status.

        Args:
            goal_id: Goal UUID
            status: New status ('active', 'completed', 'paused', 'cancelled')

        Returns:
            Updated goal data or None
        """
        if status not in ['active', 'completed', 'paused', 'cancelled']:
            logger.error(f"Invalid status: {status}")
            return None

        return await self.update_goal(goal_id, {"status": status})

    async def delete_goal(self, goal_id: str) -> bool:
        """
        Delete a goal (hard delete).

        Args:
            goal_id: Goal UUID

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            response = self.client.table("goals").delete().eq("id", goal_id).execute()

            if response.data:
                logger.info(f"Deleted goal {goal_id}")
                return True
            else:
                logger.error(f"Failed to delete goal {goal_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting goal {goal_id}: {e}")
            return False

    async def get_active_goals_count(self, user_id: int) -> int:
        """
        Get count of active goals for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Number of active goals
        """
        goals = await self.get_user_goals(user_id, status='active')
        return len(goals)

    async def get_goals_by_category(
        self,
        user_id: int,
        category: str
    ) -> List[Dict[str, Any]]:
        """
        Get goals filtered by category.

        Args:
            user_id: Telegram user ID
            category: Goal category

        Returns:
            List of goals in the category
        """
        try:
            response = self.client.table("goals") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("category", category) \
                .eq("status", "active") \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error getting goals by category: {e}")
            return []
