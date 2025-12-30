"""
Schedule repository for database operations on weekly_schedules table.
Handles schedule block creation, retrieval, and deletion.
"""

from typing import Optional, List, Dict, Any
from datetime import time
from database.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


class ScheduleRepository:
    """Repository for weekly schedule-related database operations."""

    def __init__(self):
        """Initialize schedule repository with Supabase client."""
        self.client = get_supabase()

    async def create_time_block(
        self,
        user_id: int,
        day_of_week: int,
        start_time: time,
        end_time: time,
        activity_type: str,
        description: Optional[str] = None,
        is_recurring: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new weekly schedule time block.

        Args:
            user_id: Telegram user ID
            day_of_week: Day of week (0=Monday, 6=Sunday)
            start_time: Start time
            end_time: End time
            activity_type: Type of activity (school, sport, work, personal, other)
            description: Optional description
            is_recurring: Whether this is a recurring block

        Returns:
            Dict containing created schedule block data, or None if failed
        """
        try:
            data = {
                "user_id": user_id,
                "day_of_week": day_of_week,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "activity_type": activity_type.lower(),
                "description": description,
                "is_recurring": is_recurring
            }

            response = self.client.table("weekly_schedules").insert(data).execute()

            if response.data:
                logger.info(f"Created schedule block for user {user_id} on day {day_of_week}")
                return response.data[0]
            else:
                logger.error(f"Failed to create schedule block")
                return None

        except Exception as e:
            logger.error(f"Error creating schedule block: {e}")
            return None

    async def get_schedule_block(self, block_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a schedule block by ID.

        Args:
            block_id: Schedule block UUID

        Returns:
            Dict containing schedule block data, or None if not found
        """
        try:
            response = self.client.table("weekly_schedules").select("*").eq("id", block_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error retrieving schedule block {block_id}: {e}")
            return None

    async def get_weekly_schedule(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all schedule blocks for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            List of schedule block dictionaries
        """
        try:
            response = self.client.table("weekly_schedules") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("day_of_week") \
                .order("start_time") \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving weekly schedule for user {user_id}: {e}")
            return []

    async def get_schedule_for_day(
        self,
        user_id: int,
        day_of_week: int
    ) -> List[Dict[str, Any]]:
        """
        Get schedule blocks for a specific day.

        Args:
            user_id: Telegram user ID
            day_of_week: Day of week (0=Monday, 6=Sunday)

        Returns:
            List of schedule blocks for the specified day
        """
        try:
            response = self.client.table("weekly_schedules") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("day_of_week", day_of_week) \
                .order("start_time") \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving schedule for day {day_of_week}: {e}")
            return []

    async def delete_time_block(self, block_id: str) -> bool:
        """
        Delete a schedule block.

        Args:
            block_id: Schedule block UUID

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            response = self.client.table("weekly_schedules").delete().eq("id", block_id).execute()

            if response.data:
                logger.info(f"Deleted schedule block {block_id}")
                return True
            else:
                logger.error(f"Failed to delete schedule block {block_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting schedule block {block_id}: {e}")
            return False

    async def delete_all_user_schedules(self, user_id: int) -> bool:
        """
        Delete all schedule blocks for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            response = self.client.table("weekly_schedules").delete().eq("user_id", user_id).execute()

            logger.info(f"Deleted all schedule blocks for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting all schedules for user {user_id}: {e}")
            return False

    async def check_overlap(
        self,
        user_id: int,
        day_of_week: int,
        start_time: time,
        end_time: time,
        exclude_id: Optional[str] = None
    ) -> bool:
        """
        Check if a time block overlaps with existing schedule.

        Args:
            user_id: Telegram user ID
            day_of_week: Day of week
            start_time: Proposed start time
            end_time: Proposed end time
            exclude_id: Optional schedule ID to exclude from check (for updates)

        Returns:
            True if there's an overlap, False otherwise
        """
        try:
            # Get all blocks for this day
            blocks = await self.get_schedule_for_day(user_id, day_of_week)

            # Filter out the excluded ID if provided
            if exclude_id:
                blocks = [b for b in blocks if b['id'] != exclude_id]

            # Check for overlaps
            for block in blocks:
                block_start = time.fromisoformat(block['start_time'])
                block_end = time.fromisoformat(block['end_time'])

                # Check if times overlap
                # Overlap occurs if: start < block_end AND end > block_start
                if start_time < block_end and end_time > block_start:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking schedule overlap: {e}")
            return False

    async def get_schedule_count(self, user_id: int) -> int:
        """
        Get count of schedule blocks for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Number of schedule blocks
        """
        schedules = await self.get_weekly_schedule(user_id)
        return len(schedules)

    async def get_schedules_by_activity(
        self,
        user_id: int,
        activity_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get schedule blocks filtered by activity type.

        Args:
            user_id: Telegram user ID
            activity_type: Activity type

        Returns:
            List of schedule blocks for the activity type
        """
        try:
            response = self.client.table("weekly_schedules") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("activity_type", activity_type.lower()) \
                .order("day_of_week") \
                .order("start_time") \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error getting schedules by activity: {e}")
            return []
