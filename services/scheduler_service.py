"""
Scheduler service for background jobs using APScheduler.
Handles reminder checking, daily summaries, and weekly reports.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot
from datetime import datetime, timedelta, date
from database.repositories.reminder_repository import ReminderRepository
from database.repositories.task_repository import TaskRepository
from database.repositories.user_repository import UserRepository
from services.notification_service import NotificationService
from utils.time_utils import convert_from_utc
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled background jobs."""

    def __init__(self, bot: Bot):
        """
        Initialize scheduler service.

        Args:
            bot: Telegram Bot instance
        """
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone='UTC')
        self.notification_service = NotificationService(bot)
        self.reminder_repo = ReminderRepository()
        self.task_repo = TaskRepository()
        self.user_repo = UserRepository()

    async def start(self):
        """Start the scheduler with all jobs."""
        try:
            logger.info("Starting scheduler service...")

            # Job 1: Check and send pending reminders every minute
            self.scheduler.add_job(
                self.check_and_send_reminders,
                trigger=IntervalTrigger(minutes=1),
                id='reminder_checker',
                name='Check and send pending reminders',
                replace_existing=True
            )

            # Job 2: Send daily summaries at 7 AM (runs every hour and checks user timezones)
            self.scheduler.add_job(
                self.send_daily_summaries,
                trigger=IntervalTrigger(hours=1),
                id='daily_summary',
                name='Send daily summaries',
                replace_existing=True
            )

            # Job 3: Send weekly summaries on Sundays at 8 PM UTC
            self.scheduler.add_job(
                self.send_weekly_summaries,
                trigger=CronTrigger(day_of_week='sun', hour=20, minute=0),
                id='weekly_summary',
                name='Send weekly summaries',
                replace_existing=True
            )

            # Start the scheduler
            self.scheduler.start()
            logger.info("Scheduler started successfully with 3 jobs")

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise

    async def stop(self):
        """Stop the scheduler."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    async def check_and_send_reminders(self):
        """
        Check for pending reminders and send them.
        Runs every minute.
        """
        try:
            # Get reminders due in the next 5 minutes
            check_time = datetime.utcnow() + timedelta(minutes=5)

            pending_reminders = await self.reminder_repo.get_pending_reminders(
                before_time=check_time,
                limit=100
            )

            logger.info(f"Found {len(pending_reminders)} pending reminders")

            for reminder in pending_reminders:
                try:
                    # Get task details
                    task = await self.task_repo.get_task(reminder['task_id'])

                    if task and task['status'] == 'pending':
                        # Send reminder
                        success = await self.notification_service.send_task_reminder(
                            user_id=reminder['user_id'],
                            task=task
                        )

                        if success:
                            # Mark as sent
                            await self.reminder_repo.mark_reminder_sent(reminder['id'])
                        else:
                            # Mark as failed
                            await self.reminder_repo.mark_reminder_failed(reminder['id'])
                    else:
                        # Task is not pending, cancel reminder
                        await self.reminder_repo.cancel_reminder(reminder['id'])
                        logger.info(f"Cancelled reminder for non-pending task {reminder['task_id']}")

                except Exception as e:
                    logger.error(f"Error processing reminder {reminder['id']}: {e}")
                    await self.reminder_repo.mark_reminder_failed(reminder['id'])

        except Exception as e:
            logger.error(f"Error in check_and_send_reminders: {e}")

    async def send_daily_summaries(self):
        """
        Send daily summaries to users at 7 AM their local time.
        Runs every hour to check different timezones.
        """
        try:
            # Get all active users
            users = await self.user_repo.get_all_active_users()

            current_utc = datetime.utcnow()

            for user in users:
                try:
                    # Convert current UTC time to user's timezone
                    user_tz = user.get('timezone', 'UTC')
                    user_time = convert_from_utc(current_utc, user_tz)

                    # Check if it's 7 AM in user's timezone (within current hour)
                    if user_time.hour == 7:
                        # Get today's tasks for the user
                        today = user_time.date()
                        tasks = await self.task_repo.get_tasks_for_date(user['user_id'], today)

                        # Send daily summary
                        await self.notification_service.send_daily_summary(
                            user_id=user['user_id'],
                            tasks=tasks,
                            summary_date=today
                        )

                        logger.info(f"Sent daily summary to user {user['user_id']}")

                except Exception as e:
                    logger.error(f"Error sending daily summary to user {user.get('user_id')}: {e}")

        except Exception as e:
            logger.error(f"Error in send_daily_summaries: {e}")

    async def send_weekly_summaries(self):
        """
        Send weekly progress summaries to all users.
        Runs every Sunday at 8 PM UTC.
        """
        try:
            # Get all active users
            users = await self.user_repo.get_all_active_users()

            for user in users:
                try:
                    # Get task statistics for the user
                    stats = await self.task_repo.get_task_statistics(user['user_id'])

                    # Send weekly summary
                    await self.notification_service.send_weekly_summary(
                        user_id=user['user_id'],
                        stats=stats
                    )

                    logger.info(f"Sent weekly summary to user {user['user_id']}")

                except Exception as e:
                    logger.error(f"Error sending weekly summary to user {user.get('user_id')}: {e}")

        except Exception as e:
            logger.error(f"Error in send_weekly_summaries: {e}")

    def get_scheduler_status(self) -> dict:
        """
        Get current scheduler status.

        Returns:
            Dict with scheduler status information
        """
        try:
            jobs = self.scheduler.get_jobs()

            return {
                "running": self.scheduler.running,
                "jobs_count": len(jobs),
                "jobs": [
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                    }
                    for job in jobs
                ]
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {"running": False, "jobs_count": 0, "jobs": []}
