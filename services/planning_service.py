"""
Planning service for AI-powered task generation and scheduling.
Orchestrates goal retrieval, schedule analysis, and AI plan generation.
"""

from datetime import date, timedelta, datetime, time as time_class
from typing import List, Dict, Any, Optional
from database.repositories.goal_repository import GoalRepository
from database.repositories.schedule_repository import ScheduleRepository
from database.repositories.task_repository import TaskRepository
from database.repositories.reminder_repository import ReminderRepository
from database.repositories.event_repository import EventRepository
from services.ai_service import OpenRouterAI
from utils.schedule_optimizer import ScheduleOptimizer
from utils.time_utils import get_date_range, combine_date_time, convert_to_utc
import logging

logger = logging.getLogger(__name__)


class PlanningService:
    """Service for generating AI-powered daily task plans."""

    def __init__(self):
        """Initialize planning service with required repositories."""
        self.goal_repo = GoalRepository()
        self.schedule_repo = ScheduleRepository()
        self.task_repo = TaskRepository()
        self.reminder_repo = ReminderRepository()
        self.event_repo = EventRepository()
        self.ai_service = OpenRouterAI()
        self.optimizer = ScheduleOptimizer()

    async def generate_plan(
        self,
        user_id: int,
        plan_duration_days: int = 30,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Generate a complete AI-powered plan for user's goals.

        Args:
            user_id: Telegram user ID
            plan_duration_days: Number of days to plan ahead
            timezone: User's timezone

        Returns:
            Dict containing plan summary and statistics
        """
        try:
            logger.info(f"Generating plan for user {user_id}")

            # Fetch user's data
            goals = await self.goal_repo.get_user_goals(user_id, status='active')
            weekly_schedule = await self.schedule_repo.get_weekly_schedule(user_id)

            # Validate prerequisites
            if not goals:
                return {
                    "success": False,
                    "error": "no_goals",
                    "message": "You don't have any active goals. Create a goal first with /newgoal"
                }

            # Calculate date range
            start_date = date.today()
            end_date = start_date + timedelta(days=plan_duration_days)

            # Get special events within the planning period
            special_events = await self.event_repo.get_user_events(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )

            # Call AI to generate tasks
            logger.info("Calling AI to generate task plan...")
            ai_tasks = await self.ai_service.generate_plan(
                goals=goals,
                weekly_schedule=weekly_schedule,
                special_events=special_events,
                timezone=timezone,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )

            if not ai_tasks:
                return {
                    "success": False,
                    "error": "ai_failed",
                    "message": "AI failed to generate a plan. Please try again."
                }

            # Process and save tasks
            saved_tasks = await self._process_and_save_tasks(
                user_id=user_id,
                ai_tasks=ai_tasks,
                goals=goals,
                weekly_schedule=weekly_schedule,
                special_events=special_events
            )

            logger.info(f"Generated and saved {len(saved_tasks)} tasks")

            # Create reminders for tasks
            reminders_created = await self._create_reminders_for_tasks(
                saved_tasks, timezone
            )
            logger.info(f"Created {reminders_created} reminders")

            return {
                "success": True,
                "task_count": len(saved_tasks),
                "plan_duration_days": plan_duration_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "goals_count": len(goals)
            }

        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return {
                "success": False,
                "error": "exception",
                "message": f"An error occurred: {str(e)}"
            }

    async def _process_and_save_tasks(
        self,
        user_id: int,
        ai_tasks: List[Dict[str, Any]],
        goals: List[Dict[str, Any]],
        weekly_schedule: List[Dict[str, Any]],
        special_events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process AI-generated tasks and save to database.

        Args:
            user_id: Telegram user ID
            ai_tasks: Tasks generated by AI
            goals: User's goals
            weekly_schedule: User's weekly schedule
            special_events: Special events

        Returns:
            List of saved task dictionaries
        """
        # Create goal title to ID mapping
        goal_map = {goal['title']: goal['id'] for goal in goals}

        # Process each task
        processed_tasks = []

        for ai_task in ai_tasks:
            try:
                # Find matching goal
                goal_title = ai_task.get('goal_title', '')
                goal_id = goal_map.get(goal_title)

                # If exact match not found, try fuzzy matching
                if not goal_id:
                    for title, gid in goal_map.items():
                        if goal_title.lower() in title.lower() or title.lower() in goal_title.lower():
                            goal_id = gid
                            break

                # Skip if no matching goal found
                if not goal_id:
                    logger.warning(f"No matching goal for task: {ai_task.get('title')}")
                    # Use first goal as fallback
                    if goals:
                        goal_id = goals[0]['id']
                    else:
                        continue

                # Parse date
                scheduled_date = None
                if ai_task.get('scheduled_date'):
                    try:
                        scheduled_date = date.fromisoformat(ai_task['scheduled_date'])
                    except ValueError:
                        logger.warning(f"Invalid date format: {ai_task.get('scheduled_date')}")

                # Parse time
                scheduled_time = None
                if ai_task.get('scheduled_time'):
                    try:
                        from datetime import time as time_class
                        time_parts = ai_task['scheduled_time'].split(':')
                        scheduled_time = time_class(int(time_parts[0]), int(time_parts[1]))
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid time format: {ai_task.get('scheduled_time')}")

                # Prepare task data
                task_data = {
                    "user_id": user_id,
                    "goal_id": goal_id,
                    "title": ai_task.get('title', 'Untitled task'),
                    "description": ai_task.get('description'),
                    "scheduled_date": scheduled_date.isoformat() if scheduled_date else None,
                    "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
                    "duration_minutes": ai_task.get('duration_minutes', 30),
                    "priority": ai_task.get('priority', 3),
                    "status": "pending",
                    "ai_reasoning": ai_task.get('reasoning')
                }

                processed_tasks.append(task_data)

            except Exception as e:
                logger.error(f"Error processing task: {e}")
                continue

        # Bulk save tasks
        if processed_tasks:
            saved_tasks = await self.task_repo.bulk_create_tasks(processed_tasks)
            return saved_tasks
        else:
            return []

    async def regenerate_plan(self, user_id: int, plan_duration_days: int = 30) -> Dict[str, Any]:
        """
        Delete existing pending tasks and generate a fresh plan.

        Args:
            user_id: Telegram user ID
            plan_duration_days: Number of days to plan

        Returns:
            Plan generation result
        """
        try:
            # Get all pending tasks
            pending_tasks = await self.task_repo.get_pending_tasks(user_id)

            # Delete pending tasks
            for task in pending_tasks:
                await self.task_repo.delete_task(task['id'])

            logger.info(f"Deleted {len(pending_tasks)} pending tasks for user {user_id}")

            # Generate new plan
            return await self.generate_plan(user_id, plan_duration_days)

        except Exception as e:
            logger.error(f"Error regenerating plan: {e}")
            return {
                "success": False,
                "error": "exception",
                "message": f"An error occurred: {str(e)}"
            }

    async def get_plan_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get summary of user's current plan.

        Args:
            user_id: Telegram user ID

        Returns:
            Dict with plan statistics
        """
        try:
            # Get task statistics
            stats = await self.task_repo.get_task_statistics(user_id)

            # Get upcoming tasks
            today = date.today()
            next_week = today + timedelta(days=7)
            upcoming_tasks = await self.task_repo.get_tasks_by_date(
                user_id, today, next_week
            )

            return {
                "statistics": stats,
                "upcoming_count": len(upcoming_tasks),
                "total_tasks": sum(stats.values())
            }

        except Exception as e:
            logger.error(f"Error getting plan summary: {e}")
            return {
                "statistics": {},
                "upcoming_count": 0,
                "total_tasks": 0
            }

    async def _create_reminders_for_tasks(
        self,
        tasks: List[Dict[str, Any]],
        timezone: str = "UTC"
    ) -> int:
        """
        Create reminders for a list of tasks.

        Args:
            tasks: List of saved task dictionaries
            timezone: User's timezone

        Returns:
            Number of reminders created
        """
        reminders_created = 0

        for task in tasks:
            try:
                # Skip if no scheduled date or time
                if not task.get('scheduled_date') or not task.get('scheduled_time'):
                    continue

                # Parse task datetime
                task_date = date.fromisoformat(task['scheduled_date'])
                task_time = time_class.fromisoformat(task['scheduled_time'])

                # Combine date and time in user's timezone
                task_datetime = combine_date_time(task_date, task_time, timezone)

                # Convert to UTC for storage
                task_datetime_utc = convert_to_utc(task_datetime, timezone)

                # Create reminder 15 minutes before
                reminder_time = task_datetime_utc - timedelta(minutes=15)

                # Only create reminder if it's in the future
                if reminder_time > datetime.utcnow():
                    message = f"Reminder: {task['title']}"

                    reminder = await self.reminder_repo.create_reminder(
                        user_id=task['user_id'],
                        task_id=task['id'],
                        reminder_time=reminder_time,
                        message=message
                    )

                    if reminder:
                        reminders_created += 1

                    # For high priority tasks, create additional reminder 1 day before
                    if task.get('priority', 3) >= 4:
                        day_before_reminder = task_datetime_utc - timedelta(days=1)

                        if day_before_reminder > datetime.utcnow():
                            day_before_message = f"Tomorrow: {task['title']}"

                            day_before = await self.reminder_repo.create_reminder(
                                user_id=task['user_id'],
                                task_id=task['id'],
                                reminder_time=day_before_reminder,
                                message=day_before_message
                            )

                            if day_before:
                                reminders_created += 1

            except Exception as e:
                logger.error(f"Error creating reminder for task {task.get('id')}: {e}")
                continue

        return reminders_created
