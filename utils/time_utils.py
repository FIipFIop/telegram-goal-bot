"""
Time and timezone utilities for the bot.
Handles timezone conversions and date calculations.
"""

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_user_timezone(timezone_str: str = "UTC") -> ZoneInfo:
    """
    Get timezone object from timezone string.

    Args:
        timezone_str: Timezone string (e.g., "America/New_York", "UTC")

    Returns:
        ZoneInfo timezone object
    """
    try:
        return ZoneInfo(timezone_str)
    except Exception as e:
        logger.warning(f"Invalid timezone {timezone_str}, using UTC: {e}")
        return ZoneInfo("UTC")


def convert_to_utc(dt: datetime, from_timezone: str) -> datetime:
    """
    Convert datetime from user's timezone to UTC.

    Args:
        dt: Datetime object (naive)
        from_timezone: User's timezone string

    Returns:
        Datetime in UTC with timezone info
    """
    try:
        user_tz = get_user_timezone(from_timezone)
        # Make datetime aware in user's timezone
        dt_aware = dt.replace(tzinfo=user_tz)
        # Convert to UTC
        return dt_aware.astimezone(ZoneInfo("UTC"))
    except Exception as e:
        logger.error(f"Error converting to UTC: {e}")
        return dt.replace(tzinfo=ZoneInfo("UTC"))


def convert_from_utc(dt: datetime, to_timezone: str) -> datetime:
    """
    Convert datetime from UTC to user's timezone.

    Args:
        dt: Datetime object in UTC
        to_timezone: Target timezone string

    Returns:
        Datetime in user's timezone
    """
    try:
        user_tz = get_user_timezone(to_timezone)
        # Ensure dt is UTC aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        # Convert to user's timezone
        return dt.astimezone(user_tz)
    except Exception as e:
        logger.error(f"Error converting from UTC: {e}")
        return dt


def get_current_time_for_user(timezone_str: str = "UTC") -> datetime:
    """
    Get current time in user's timezone.

    Args:
        timezone_str: User's timezone string

    Returns:
        Current datetime in user's timezone
    """
    user_tz = get_user_timezone(timezone_str)
    return datetime.now(user_tz)


def get_date_range(start_date: date, days: int) -> list[date]:
    """
    Generate list of dates starting from start_date.

    Args:
        start_date: Starting date
        days: Number of days to generate

    Returns:
        List of date objects
    """
    return [start_date + timedelta(days=i) for i in range(days)]


def get_day_of_week(d: date) -> int:
    """
    Get day of week for a date.

    Args:
        d: Date object

    Returns:
        Day of week (0=Monday, 6=Sunday)
    """
    return d.weekday()


def is_same_day(dt1: datetime, dt2: datetime) -> bool:
    """
    Check if two datetimes are on the same day.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        True if same day, False otherwise
    """
    return dt1.date() == dt2.date()


def combine_date_time(d: date, t: time, timezone_str: str = "UTC") -> datetime:
    """
    Combine date and time into datetime with timezone.

    Args:
        d: Date object
        t: Time object
        timezone_str: Timezone string

    Returns:
        Datetime object with timezone
    """
    tz = get_user_timezone(timezone_str)
    return datetime.combine(d, t, tzinfo=tz)


def parse_relative_date(date_str: str, base_date: Optional[date] = None) -> Optional[date]:
    """
    Parse relative date strings like "today", "tomorrow", "next week".

    Args:
        date_str: Date string
        base_date: Base date (default: today)

    Returns:
        Date object or None
    """
    if base_date is None:
        base_date = date.today()

    date_str = date_str.lower().strip()

    if date_str == "today":
        return base_date
    elif date_str == "tomorrow":
        return base_date + timedelta(days=1)
    elif date_str == "yesterday":
        return base_date - timedelta(days=1)
    elif date_str == "next week":
        return base_date + timedelta(days=7)
    elif date_str == "next month":
        # Approximate - add 30 days
        return base_date + timedelta(days=30)

    return None


def get_week_dates(reference_date: Optional[date] = None) -> tuple[date, date]:
    """
    Get start and end dates of the week containing reference_date.

    Args:
        reference_date: Reference date (default: today)

    Returns:
        Tuple of (week_start, week_end) where week starts on Monday
    """
    if reference_date is None:
        reference_date = date.today()

    # Get Monday of the week
    days_since_monday = reference_date.weekday()
    week_start = reference_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)

    return week_start, week_end


def get_month_dates(reference_date: Optional[date] = None) -> tuple[date, date]:
    """
    Get start and end dates of the month containing reference_date.

    Args:
        reference_date: Reference date (default: today)

    Returns:
        Tuple of (month_start, month_end)
    """
    if reference_date is None:
        reference_date = date.today()

    # First day of month
    month_start = reference_date.replace(day=1)

    # Last day of month
    if reference_date.month == 12:
        next_month = reference_date.replace(year=reference_date.year + 1, month=1, day=1)
    else:
        next_month = reference_date.replace(month=reference_date.month + 1, day=1)

    month_end = next_month - timedelta(days=1)

    return month_start, month_end


def format_datetime_for_display(dt: datetime, timezone_str: str = "UTC") -> str:
    """
    Format datetime for user-friendly display.

    Args:
        dt: Datetime object
        timezone_str: User's timezone

    Returns:
        Formatted string (e.g., "Mon, Jan 15 at 2:30 PM")
    """
    # Convert to user's timezone
    user_dt = convert_from_utc(dt, timezone_str)

    return user_dt.strftime("%a, %b %d at %I:%M %p")


def format_date_for_display(d: date) -> str:
    """
    Format date for user-friendly display.

    Args:
        d: Date object

    Returns:
        Formatted string (e.g., "Monday, January 15, 2025")
    """
    return d.strftime("%A, %B %d, %Y")


def get_days_until(target_date: date, from_date: Optional[date] = None) -> int:
    """
    Get number of days until target date.

    Args:
        target_date: Target date
        from_date: Starting date (default: today)

    Returns:
        Number of days (negative if target is in the past)
    """
    if from_date is None:
        from_date = date.today()

    delta = target_date - from_date
    return delta.days


def is_past_date(d: date) -> bool:
    """
    Check if date is in the past.

    Args:
        d: Date to check

    Returns:
        True if date is before today
    """
    return d < date.today()


def is_future_date(d: date) -> bool:
    """
    Check if date is in the future.

    Args:
        d: Date to check

    Returns:
        True if date is after today
    """
    return d > date.today()
