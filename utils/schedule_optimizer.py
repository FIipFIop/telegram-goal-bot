"""
Schedule optimizer utility for calculating available time slots.
Helps determine when tasks can be scheduled based on user's availability.
"""

from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimeSlot:
    """Represents an available time slot."""
    start_time: time
    end_time: time
    duration_minutes: int


class ScheduleOptimizer:
    """Optimizer for finding available time slots in user's schedule."""

    # Default working hours (7 AM - 11 PM)
    DEFAULT_DAY_START = time(7, 0)
    DEFAULT_DAY_END = time(23, 0)

    def __init__(self):
        """Initialize schedule optimizer."""
        pass

    def get_available_slots_for_date(
        self,
        target_date: date,
        weekly_schedule: List[Dict[str, Any]],
        special_events: List[Dict[str, Any]],
        min_duration_minutes: int = 15
    ) -> List[TimeSlot]:
        """
        Calculate available time slots for a specific date.

        Args:
            target_date: Date to calculate slots for
            weekly_schedule: List of recurring weekly schedule blocks
            special_events: List of special one-time events
            min_duration_minutes: Minimum slot duration to include

        Returns:
            List of TimeSlot objects representing available times
        """
        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = target_date.weekday()

        # Start with full day as available
        available_periods = [(self.DEFAULT_DAY_START, self.DEFAULT_DAY_END)]

        # Remove weekly schedule blocks for this day
        for block in weekly_schedule:
            if block['day_of_week'] == day_of_week:
                block_start = self._parse_time(block['start_time'])
                block_end = self._parse_time(block['end_time'])

                available_periods = self._remove_time_period(
                    available_periods,
                    block_start,
                    block_end
                )

        # Remove special events on this date
        for event in special_events:
            event_date = self._parse_date(event['event_date'])

            if event_date == target_date and event.get('blocks_scheduling', True):
                if event.get('is_all_day', False):
                    # All-day event - no slots available
                    return []

                if event.get('start_time') and event.get('end_time'):
                    event_start = self._parse_time(event['start_time'])
                    event_end = self._parse_time(event['end_time'])

                    available_periods = self._remove_time_period(
                        available_periods,
                        event_start,
                        event_end
                    )

        # Convert periods to TimeSlot objects
        slots = []
        for start, end in available_periods:
            duration = self._calculate_duration_minutes(start, end)

            if duration >= min_duration_minutes:
                slots.append(TimeSlot(
                    start_time=start,
                    end_time=end,
                    duration_minutes=duration
                ))

        return slots

    def find_best_slot_for_task(
        self,
        available_slots: List[TimeSlot],
        task_duration: int,
        preferred_time: str = "any"
    ) -> Tuple[Optional[time], Optional[str]]:
        """
        Find the best time slot for a task.

        Args:
            available_slots: List of available time slots
            task_duration: Required duration in minutes
            preferred_time: Preference - "morning", "afternoon", "evening", or "any"

        Returns:
            Tuple of (suggested_time, reasoning) or (None, None)
        """
        if not available_slots:
            return None, "No available time slots"

        # Filter slots that can fit the task
        suitable_slots = [
            slot for slot in available_slots
            if slot.duration_minutes >= task_duration
        ]

        if not suitable_slots:
            return None, f"No slots large enough for {task_duration} minute task"

        # Apply preference
        if preferred_time == "morning":
            # Prefer slots starting before noon
            preferred = [s for s in suitable_slots if s.start_time < time(12, 0)]
            if preferred:
                slot = preferred[0]
                return slot.start_time, "Scheduled in the morning as preferred"

        elif preferred_time == "afternoon":
            # Prefer slots starting between noon and 6 PM
            preferred = [s for s in suitable_slots
                        if time(12, 0) <= s.start_time < time(18, 0)]
            if preferred:
                slot = preferred[0]
                return slot.start_time, "Scheduled in the afternoon as preferred"

        elif preferred_time == "evening":
            # Prefer slots starting after 6 PM
            preferred = [s for s in suitable_slots if s.start_time >= time(18, 0)]
            if preferred:
                slot = preferred[0]
                return slot.start_time, "Scheduled in the evening as preferred"

        # Default: use first available slot
        slot = suitable_slots[0]
        return slot.start_time, f"Best available time slot ({slot.duration_minutes} min available)"

    def calculate_total_available_minutes(
        self,
        slots: List[TimeSlot]
    ) -> int:
        """
        Calculate total available minutes across all slots.

        Args:
            slots: List of time slots

        Returns:
            Total minutes available
        """
        return sum(slot.duration_minutes for slot in slots)

    def _remove_time_period(
        self,
        periods: List[Tuple[time, time]],
        remove_start: time,
        remove_end: time
    ) -> List[Tuple[time, time]]:
        """
        Remove a time period from list of available periods.

        Args:
            periods: List of (start, end) time tuples
            remove_start: Start of period to remove
            remove_end: End of period to remove

        Returns:
            Updated list of periods
        """
        result = []

        for period_start, period_end in periods:
            # No overlap
            if remove_end <= period_start or remove_start >= period_end:
                result.append((period_start, period_end))
                continue

            # Partial overlap - split into available parts
            if period_start < remove_start < period_end:
                # Keep the part before removed period
                result.append((period_start, remove_start))

            if period_start < remove_end < period_end:
                # Keep the part after removed period
                result.append((remove_end, period_end))

        return result

    def _parse_time(self, time_value: Any) -> time:
        """Parse time from various formats."""
        if isinstance(time_value, time):
            return time_value
        elif isinstance(time_value, str):
            # Handle ISO format (HH:MM:SS or HH:MM)
            parts = time_value.split(':')
            return time(int(parts[0]), int(parts[1]))
        else:
            logger.warning(f"Unknown time format: {time_value}")
            return time(0, 0)

    def _parse_date(self, date_value: Any) -> date:
        """Parse date from various formats."""
        if isinstance(date_value, date):
            return date_value
        elif isinstance(date_value, str):
            # Handle ISO format (YYYY-MM-DD)
            return datetime.fromisoformat(date_value).date()
        else:
            logger.warning(f"Unknown date format: {date_value}")
            return date.today()

    def _calculate_duration_minutes(self, start: time, end: time) -> int:
        """Calculate duration in minutes between two times."""
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute

        # Handle case where end is before start (crosses midnight)
        if end_minutes < start_minutes:
            end_minutes += 24 * 60

        return end_minutes - start_minutes

    def distribute_tasks_across_days(
        self,
        tasks: List[Dict[str, Any]],
        available_days: List[date],
        max_tasks_per_day: int = 5
    ) -> Dict[date, List[Dict[str, Any]]]:
        """
        Distribute tasks across available days.

        Args:
            tasks: List of tasks to distribute
            available_days: List of dates to distribute across
            max_tasks_per_day: Maximum tasks per day

        Returns:
            Dict mapping date to list of tasks
        """
        distribution = {day: [] for day in available_days}

        # Sort tasks by priority (higher first)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: t.get('priority', 3),
            reverse=True
        )

        # Simple round-robin distribution
        day_index = 0
        for task in sorted_tasks:
            current_day = available_days[day_index % len(available_days)]

            # Check if day has capacity
            if len(distribution[current_day]) < max_tasks_per_day:
                distribution[current_day].append(task)
                day_index += 1
            else:
                # Move to next day
                day_index += 1
                current_day = available_days[day_index % len(available_days)]
                distribution[current_day].append(task)

        return distribution
