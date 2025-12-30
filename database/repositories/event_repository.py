"""
Event repository for database operations on special_events table.
Handles special event creation, retrieval, updates, and deletion.
"""

from typing import Optional, List, Dict, Any
from datetime import date, time
from database.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


class EventRepository:
    """Repository for special event-related database operations."""

    def __init__(self):
        """Initialize event repository with Supabase client."""
        self.client = get_supabase()

    async def create_event(
        self,
        user_id: int,
        title: str,
        event_date: date,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        description: Optional[str] = None,
        is_all_day: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new special event.

        Args:
            user_id: Telegram user ID
            title: Event title
            event_date: Date of the event
            start_time: Optional start time
            end_time: Optional end time
            description: Optional event description
            is_all_day: Whether it's an all-day event

        Returns:
            Dict containing created event data, or None if failed
        """
        try:
            data = {
                "user_id": user_id,
                "title": title,
                "event_date": event_date.isoformat(),
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "description": description,
                "is_all_day": is_all_day
            }

            response = self.client.table("special_events").insert(data).execute()

            if response.data:
                logger.info(f"Created event '{title}' for user {user_id}")
                return response.data[0]
            else:
                logger.error(f"Failed to create event")
                return None

        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an event by ID.

        Args:
            event_id: Event UUID

        Returns:
            Dict containing event data, or None if not found
        """
        try:
            response = self.client.table("special_events").select("*").eq("id", event_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error retrieving event {event_id}: {e}")
            return None

    async def get_user_events(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a user, optionally filtered by date range.

        Args:
            user_id: Telegram user ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of event dictionaries
        """
        try:
            query = self.client.table("special_events") \
                .select("*") \
                .eq("user_id", user_id)

            if start_date:
                query = query.gte("event_date", start_date.isoformat())

            if end_date:
                query = query.lte("event_date", end_date.isoformat())

            query = query.order("event_date")

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving user events: {e}")
            return []

    async def get_events_for_date(
        self,
        user_id: int,
        event_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a specific date.

        Args:
            user_id: Telegram user ID
            event_date: Date to get events for

        Returns:
            List of events on that date
        """
        try:
            response = self.client.table("special_events") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("event_date", event_date.isoformat()) \
                .order("start_time") \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving events for date: {e}")
            return []

    async def update_event(
        self,
        event_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update an event.

        Args:
            event_id: Event UUID
            **kwargs: Fields to update (title, event_date, start_time, end_time, description, is_all_day)

        Returns:
            Updated event data or None
        """
        try:
            # Filter out None values
            updates = {k: v for k, v in kwargs.items() if v is not None}

            # Convert date/time objects to ISO format
            if 'event_date' in updates and isinstance(updates['event_date'], date):
                updates['event_date'] = updates['event_date'].isoformat()

            if 'start_time' in updates and isinstance(updates['start_time'], time):
                updates['start_time'] = updates['start_time'].isoformat()

            if 'end_time' in updates and isinstance(updates['end_time'], time):
                updates['end_time'] = updates['end_time'].isoformat()

            if not updates:
                logger.warning("No valid updates provided")
                return None

            response = self.client.table("special_events").update(updates).eq("id", event_id).execute()

            if response.data:
                logger.info(f"Updated event {event_id}")
                return response.data[0]
            else:
                logger.error(f"Failed to update event {event_id}")
                return None

        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return None

    async def delete_event(self, event_id: str) -> bool:
        """
        Delete an event.

        Args:
            event_id: Event UUID

        Returns:
            True if deletion successful
        """
        try:
            response = self.client.table("special_events").delete().eq("id", event_id).execute()

            if response.data:
                logger.info(f"Deleted event {event_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False

    async def check_event_conflict(
        self,
        user_id: int,
        event_date: date,
        start_time: Optional[time],
        end_time: Optional[time],
        exclude_event_id: Optional[str] = None
    ) -> bool:
        """
        Check if a new event conflicts with existing events.

        Args:
            user_id: Telegram user ID
            event_date: Date of the event
            start_time: Start time
            end_time: End time
            exclude_event_id: Optional event ID to exclude (for updates)

        Returns:
            True if conflict exists, False otherwise
        """
        try:
            # Get all events on that date
            events = await self.get_events_for_date(user_id, event_date)

            # Filter out the excluded event if provided
            if exclude_event_id:
                events = [e for e in events if e['id'] != exclude_event_id]

            # If no start/end time (all-day event), check for any all-day events
            if not start_time or not end_time:
                return any(e.get('is_all_day', False) for e in events)

            # Check for time overlaps
            for event in events:
                # If existing event is all-day, there's a conflict
                if event.get('is_all_day', False):
                    return True

                # If existing event has no times, skip
                if not event.get('start_time') or not event.get('end_time'):
                    continue

                event_start = time.fromisoformat(event['start_time'])
                event_end = time.fromisoformat(event['end_time'])

                # Check for overlap
                if (start_time < event_end and end_time > event_start):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking event conflict: {e}")
            return False

    async def get_upcoming_events(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming events for a user.

        Args:
            user_id: Telegram user ID
            limit: Maximum number of events to return

        Returns:
            List of upcoming events
        """
        try:
            today = date.today()

            response = self.client.table("special_events") \
                .select("*") \
                .eq("user_id", user_id) \
                .gte("event_date", today.isoformat()) \
                .order("event_date") \
                .limit(limit) \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving upcoming events: {e}")
            return []

    async def get_event_count(self, user_id: int) -> int:
        """
        Get total count of events for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Count of events
        """
        try:
            response = self.client.table("special_events") \
                .select("id", count="exact") \
                .eq("user_id", user_id) \
                .execute()

            return response.count if response.count else 0

        except Exception as e:
            logger.error(f"Error getting event count: {e}")
            return 0
