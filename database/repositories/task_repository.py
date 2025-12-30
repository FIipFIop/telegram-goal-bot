"""
Task repository for database operations on daily_tasks table.
Handles task creation, retrieval, updates, and completion tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import date, time, datetime
from database.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


class TaskRepository:
    """Repository for daily task-related database operations."""

    def __init__(self):
        """Initialize task repository with Supabase client."""
        self.client = get_supabase()

    async def create_task(
        self,
        user_id: int,
        goal_id: str,
        title: str,
        description: Optional[str] = None,
        scheduled_date: Optional[date] = None,
        scheduled_time: Optional[time] = None,
        duration_minutes: int = 30,
        priority: int = 3,
        ai_reasoning: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new daily task.

        Args:
            user_id: Telegram user ID
            goal_id: Related goal UUID
            title: Task title
            description: Task description
            scheduled_date: Date when task should be done
            scheduled_time: Suggested time for task
            duration_minutes: Estimated duration
            priority: Priority (1-5)
            ai_reasoning: AI's reasoning for this task/timing

        Returns:
            Dict containing created task data, or None if failed
        """
        try:
            data = {
                "user_id": user_id,
                "goal_id": goal_id,
                "title": title,
                "description": description,
                "scheduled_date": scheduled_date.isoformat() if scheduled_date else None,
                "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
                "duration_minutes": duration_minutes,
                "priority": priority,
                "status": "pending",
                "ai_reasoning": ai_reasoning
            }

            response = self.client.table("daily_tasks").insert(data).execute()

            if response.data:
                logger.info(f"Created task '{title}' for user {user_id}")
                return response.data[0]
            else:
                logger.error(f"Failed to create task '{title}'")
                return None

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None

    async def bulk_create_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple tasks at once.

        Args:
            tasks: List of task dictionaries

        Returns:
            List of created task dictionaries
        """
        try:
            response = self.client.table("daily_tasks").insert(tasks).execute()

            if response.data:
                logger.info(f"Bulk created {len(response.data)} tasks")
                return response.data
            else:
                logger.error("Failed to bulk create tasks")
                return []

        except Exception as e:
            logger.error(f"Error bulk creating tasks: {e}")
            return []

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task by ID.

        Args:
            task_id: Task UUID

        Returns:
            Dict containing task data, or None if not found
        """
        try:
            response = self.client.table("daily_tasks").select("*").eq("id", task_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {e}")
            return None

    async def get_tasks_by_date(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get tasks within a date range.

        Args:
            user_id: Telegram user ID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of task dictionaries
        """
        try:
            response = self.client.table("daily_tasks") \
                .select("*, goals(title)") \
                .eq("user_id", user_id) \
                .gte("scheduled_date", start_date.isoformat()) \
                .lte("scheduled_date", end_date.isoformat()) \
                .order("scheduled_date") \
                .order("scheduled_time") \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving tasks by date: {e}")
            return []

    async def get_tasks_for_date(
        self,
        user_id: int,
        target_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks for a specific date.

        Args:
            user_id: Telegram user ID
            target_date: Target date

        Returns:
            List of tasks for the date
        """
        return await self.get_tasks_by_date(user_id, target_date, target_date)

    async def get_pending_tasks(
        self,
        user_id: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending (uncompleted) tasks for a user.

        Args:
            user_id: Telegram user ID
            limit: Optional limit on number of tasks

        Returns:
            List of pending tasks
        """
        try:
            query = self.client.table("daily_tasks") \
                .select("*, goals(title)") \
                .eq("user_id", user_id) \
                .eq("status", "pending") \
                .order("scheduled_date") \
                .order("priority", desc=True)

            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving pending tasks: {e}")
            return []

    async def get_tasks_by_goal(
        self,
        goal_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks for a specific goal.

        Args:
            goal_id: Goal UUID

        Returns:
            List of tasks for the goal
        """
        try:
            response = self.client.table("daily_tasks") \
                .select("*") \
                .eq("goal_id", goal_id) \
                .order("scheduled_date") \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving tasks for goal: {e}")
            return []

    async def update_task(
        self,
        task_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a task.

        Args:
            task_id: Task UUID
            updates: Dictionary of fields to update

        Returns:
            Dict containing updated task data, or None if failed
        """
        try:
            response = self.client.table("daily_tasks").update(updates).eq("id", task_id).execute()

            if response.data:
                logger.info(f"Updated task {task_id}")
                return response.data[0]
            else:
                logger.error(f"Failed to update task {task_id}")
                return None

        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return None

    async def mark_task_complete(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Mark a task as completed.

        Args:
            task_id: Task UUID

        Returns:
            Updated task data or None
        """
        updates = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }
        return await self.update_task(task_id, updates)

    async def mark_task_skipped(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Mark a task as skipped.

        Args:
            task_id: Task UUID

        Returns:
            Updated task data or None
        """
        return await self.update_task(task_id, {"status": "skipped"})

    async def reschedule_task(
        self,
        task_id: str,
        new_date: date,
        new_time: Optional[time] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Reschedule a task to a new date/time.

        Args:
            task_id: Task UUID
            new_date: New scheduled date
            new_time: Optional new scheduled time

        Returns:
            Updated task data or None
        """
        updates = {
            "scheduled_date": new_date.isoformat(),
            "status": "rescheduled"
        }

        if new_time:
            updates["scheduled_time"] = new_time.isoformat()

        return await self.update_task(task_id, updates)

    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task UUID

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            response = self.client.table("daily_tasks").delete().eq("id", task_id).execute()

            if response.data:
                logger.info(f"Deleted task {task_id}")
                return True
            else:
                logger.error(f"Failed to delete task {task_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False

    async def delete_tasks_by_goal(self, goal_id: str) -> bool:
        """
        Delete all tasks for a goal.

        Args:
            goal_id: Goal UUID

        Returns:
            True if deletion successful
        """
        try:
            response = self.client.table("daily_tasks").delete().eq("goal_id", goal_id).execute()
            logger.info(f"Deleted tasks for goal {goal_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting tasks for goal: {e}")
            return False

    async def get_task_statistics(self, user_id: int) -> Dict[str, int]:
        """
        Get task statistics for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Dict with counts of tasks by status
        """
        try:
            response = self.client.table("daily_tasks") \
                .select("status") \
                .eq("user_id", user_id) \
                .execute()

            if not response.data:
                return {"pending": 0, "completed": 0, "skipped": 0, "rescheduled": 0}

            stats = {"pending": 0, "completed": 0, "skipped": 0, "rescheduled": 0}
            for task in response.data:
                status = task.get("status", "pending")
                stats[status] = stats.get(status, 0) + 1

            return stats

        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {"pending": 0, "completed": 0, "skipped": 0, "rescheduled": 0}
