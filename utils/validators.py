"""
Input validation utilities for the bot.
Validates time, date, and other user inputs.
"""

import re
from datetime import datetime, time, date
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def validate_time_format(time_str: str) -> Tuple[bool, Optional[time], str]:
    """
    Validate and parse time string in HH:MM format.

    Args:
        time_str: Time string (e.g., "14:30", "09:00")

    Returns:
        Tuple of (is_valid, parsed_time, error_message)
    """
    # Remove whitespace
    time_str = time_str.strip()

    # Try multiple formats
    formats = [
        "%H:%M",      # 14:30
        "%I:%M %p",   # 2:30 PM
        "%I:%M%p",    # 2:30PM
        "%H.%M",      # 14.30
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return (True, dt.time(), "")
        except ValueError:
            continue

    # Try flexible parsing with regex
    # Match patterns like: 14:30, 2:30pm, 2pm, 14.30
    pattern = r'^(\d{1,2})[:\.]?(\d{2})?\s*(am|pm)?$'
    match = re.match(pattern, time_str.lower())

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)

        # Handle AM/PM
        if period == 'pm' and hour < 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0

        # Validate ranges
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (True, time(hour, minute), "")

    return (False, None, "Invalid time format. Please use HH:MM (e.g., 14:30)")


def validate_time_range(start_time: time, end_time: time) -> Tuple[bool, str]:
    """
    Validate that end time is after start time.

    Args:
        start_time: Start time
        end_time: End time

    Returns:
        Tuple of (is_valid, error_message)
    """
    if end_time > start_time:
        return (True, "")
    else:
        return (False, "End time must be after start time")


def validate_date_format(date_str: str) -> Tuple[bool, Optional[date], str]:
    """
    Validate and parse date string.

    Args:
        date_str: Date string (e.g., "2025-12-31", "31/12/2025")

    Returns:
        Tuple of (is_valid, parsed_date, error_message)
    """
    # Remove whitespace
    date_str = date_str.strip()

    # Try multiple formats
    formats = [
        "%Y-%m-%d",    # 2025-12-31
        "%d/%m/%Y",    # 31/12/2025
        "%m/%d/%Y",    # 12/31/2025
        "%d-%m-%Y",    # 31-12-2025
        "%Y/%m/%d",    # 2025/12/31
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt).date()
            return (True, parsed, "")
        except ValueError:
            continue

    return (False, None, "Invalid date format. Please use YYYY-MM-DD (e.g., 2025-01-15)")


def validate_priority(priority: int) -> bool:
    """
    Validate priority value.

    Args:
        priority: Priority value

    Returns:
        True if valid (1-5), False otherwise
    """
    return isinstance(priority, int) and 1 <= priority <= 5


def validate_day_of_week(day: int) -> bool:
    """
    Validate day of week value.

    Args:
        day: Day of week (0=Monday, 6=Sunday)

    Returns:
        True if valid (0-6), False otherwise
    """
    return isinstance(day, int) and 0 <= day <= 6


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse duration string to minutes.

    Args:
        duration_str: Duration string (e.g., "30", "1h", "1.5h", "90m")

    Returns:
        Duration in minutes, or None if invalid
    """
    duration_str = duration_str.strip().lower()

    # Just a number (assume minutes)
    if duration_str.isdigit():
        return int(duration_str)

    # Pattern: 1h, 1.5h, 90m, 1h30m
    pattern = r'^(\d+(?:\.\d+)?)\s*([hm])(?:\s*(\d+)\s*m)?$'
    match = re.match(pattern, duration_str)

    if match:
        value = float(match.group(1))
        unit = match.group(2)
        extra_minutes = int(match.group(3)) if match.group(3) else 0

        if unit == 'h':
            return int(value * 60) + extra_minutes
        elif unit == 'm':
            return int(value)

    return None


def format_time_12h(t: time) -> str:
    """
    Format time object to 12-hour format string.

    Args:
        t: time object

    Returns:
        Formatted time string (e.g., "2:30 PM")
    """
    return t.strftime("%I:%M %p").lstrip('0')


def format_time_24h(t: time) -> str:
    """
    Format time object to 24-hour format string.

    Args:
        t: time object

    Returns:
        Formatted time string (e.g., "14:30")
    """
    return t.strftime("%H:%M")


def get_day_name(day_index: int) -> str:
    """
    Get day name from day index.

    Args:
        day_index: Day of week (0=Monday, 6=Sunday)

    Returns:
        Day name (e.g., "Monday")
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if 0 <= day_index <= 6:
        return days[day_index]
    return "Unknown"


def get_day_short_name(day_index: int) -> str:
    """
    Get short day name from day index.

    Args:
        day_index: Day of week (0=Monday, 6=Sunday)

    Returns:
        Short day name (e.g., "Mon")
    """
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if 0 <= day_index <= 6:
        return days[day_index]
    return "?"


def validate_activity_type(activity_type: str) -> bool:
    """
    Validate activity type.

    Args:
        activity_type: Activity type string

    Returns:
        True if valid, False otherwise
    """
    valid_types = ['school', 'sport', 'work', 'personal', 'other']
    return activity_type.lower() in valid_types
