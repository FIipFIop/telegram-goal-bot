"""
Reminder repository for database operations on reminders table.
Handles reminder creation, retrieval, and status updates.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from database.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


class ReminderRepository:
    """Repository for reminder-related database operations."""

    def __init__(self):
        """Initialize reminder repository with Supabase client."""
        self.client = get_supabase()

    async def create_reminder(
        self,
        user_id: int,
        task_id: str,
        reminder_time: datetime,
        message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new reminder.

        Args:
            user_id: Telegram user ID
            task_id: Related task UUID
            reminder_time: When to send reminder (UTC)
            message: Reminder message text

        Returns:
            Dict containing created reminder data, or None if failed
        """
        try:
            data = {
                "user_id": user_id,
                "task_id": task_id,
                "reminder_time": reminder_time.isoformat(),
                "message": message,
                "status": "pending"
            }

            response = self.client.table("reminders").insert(data).execute()

            if response.data:
                logger.info(f"Created reminder for user {user_id} at {reminder_time}")
                return response.data[0]
            else:
                logger.error(f"Failed to create reminder")
                return None

        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return None

    async def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a reminder by ID.

        Args:
            reminder_id: Reminder UUID

        Returns:
            Dict containing reminder data, or None if not found
        """
        try:
            response = self.client.table("reminders").select("*").eq("id", reminder_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error retrieving reminder {reminder_id}: {e}")
            return None

    async def get_pending_reminders(
        self,
        before_time: datetime,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending reminders that are due before specified time.

        Args:
            before_time: Get reminders before this time (UTC)
            limit: Optional limit on number of reminders

        Returns:
            List of pending reminder dictionaries
        """
        try:
            query = self.client.table("reminders") \
                .select("*") \
                .eq("status", "pending") \
                .lte("reminder_time", before_time.isoformat()) \
                .order("reminder_time")

            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving pending reminders: {e}")
            return []

    async def get_user_reminders(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get reminders for a specific user.

        Args:
            user_id: Telegram user ID
            status: Optional status filter ('pending', 'sent', 'failed', 'cancelled')
            limit: Maximum number of reminders to return

        Returns:
            List of reminder dictionaries
        """
        try:
            query = self.client.table("reminders") \
                .select("*") \
                .eq("user_id", user_id)

            if status:
                query = query.eq("status", status)

            query = query.order("reminder_time", desc=True).limit(limit)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving user reminders: {e}")
            return []

    async def get_task_reminders(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all reminders for a specific task.

        Args:
            task_id: Task UUID

        Returns:
            List of reminders for the task
        """
        try:
            response = self.client.table("reminders") \
                .select("*") \
                .eq("task_id", task_id) \
                .order("reminder_time") \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving task reminders: {e}")
            return []

    async def mark_reminder_sent(
        self,
        reminder_id: str,
        sent_at: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Mark a reminder as sent.

        Args:
            reminder_id: Reminder UUID
            sent_at: Time when sent (default: now)

        Returns:
            Updated reminder data or None
        """
        try:
            if sent_at is None:
                sent_at = datetime.utcnow()

            updates = {
                "status": "sent",
                "sent_at": sent_at.isoformat()
            }

            response = self.client.table("reminders").update(updates).eq("id", reminder_id).execute()

            if response.data:
                logger.info(f"Marked reminder {reminder_id} as sent")
                return response.data[0]
            else:
                logger.error(f"Failed to mark reminder {reminder_id} as sent")
                return None

        except Exception as e:
            logger.error(f"Error marking reminder as sent: {e}")
            return None

    async def mark_reminder_failed(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """
        Mark a reminder as failed.

        Args:
            reminder_id: Reminder UUID

        Returns:
            Updated reminder data or None
        """
        try:
            response = self.client.table("reminders") \
                .update({"status": "failed"}) \
                .eq("id", reminder_id) \
                .execute()

            if response.data:
                logger.info(f"Marked reminder {reminder_id} as failed")
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error marking reminder as failed: {e}")
            return None

    async def cancel_reminder(self, reminder_id: str) -> bool:
        """
        Cancel a pending reminder.

        Args:
            reminder_id: Reminder UUID

        Returns:
            True if cancellation successful
        """
        try:
            response = self.client.table("reminders") \
                .update({"status": "cancelled"}) \
                .eq("id", reminder_id) \
                .execute()

            if response.data:
                logger.info(f"Cancelled reminder {reminder_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error cancelling reminder: {e}")
            return False

    async def delete_reminder(self, reminder_id: str) -> bool:
        """
        Delete a reminder.

        Args:
            reminder_id: Reminder UUID

        Returns:
            True if deletion successful
        """
        try:
            response = self.client.table("reminders").delete().eq("id", reminder_id).execute()

            if response.data:
                logger.info(f"Deleted reminder {reminder_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return False

    async def delete_task_reminders(self, task_id: str) -> bool:
        """
        Delete all reminders for a task.

        Args:
            task_id: Task UUID

        Returns:
            True if deletion successful
        """
        try:
            response = self.client.table("reminders").delete().eq("task_id", task_id).execute()
            logger.info(f"Deleted reminders for task {task_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting task reminders: {e}")
            return False

    async def get_reminder_statistics(self, user_id: int) -> Dict[str, int]:
        """
        Get reminder statistics for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Dict with counts of reminders by status
        """
        try:
            response = self.client.table("reminders") \
                .select("status") \
                .eq("user_id", user_id) \
                .execute()

            if not response.data:
                return {"pending": 0, "sent": 0, "failed": 0, "cancelled": 0}

            stats = {"pending": 0, "sent": 0, "failed": 0, "cancelled": 0}
            for reminder in response.data:
                status = reminder.get("status", "pending")
                stats[status] = stats.get(status, 0) + 1

            return stats

        except Exception as e:
            logger.error(f"Error getting reminder statistics: {e}")
            return {"pending": 0, "sent": 0, "failed": 0, "cancelled": 0}
