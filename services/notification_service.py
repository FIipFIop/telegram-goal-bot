"""
Notification service for sending reminders and messages via Telegram.
Handles formatting and sending of task reminders and summaries.
"""

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from typing import Dict, Any, List
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via Telegram bot."""

    def __init__(self, bot: Bot):
        """
        Initialize notification service.

        Args:
            bot: Telegram Bot instance
        """
        self.bot = bot

    async def send_task_reminder(
        self,
        user_id: int,
        task: Dict[str, Any]
    ) -> bool:
        """
        Send a task reminder notification.

        Args:
            user_id: Telegram user ID
            task: Task dictionary with details

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Format reminder message
            title = task.get('title', 'Task')
            scheduled_time = task.get('scheduled_time', '')
            duration = task.get('duration_minutes', 30)

            time_str = scheduled_time[:5] if scheduled_time else 'soon'

            message = (
                f"⏰ *Task Reminder*\n\n"
                f"*{title}*\n\n"
                f"🕐 Scheduled: {time_str}\n"
                f"⏱️ Duration: {duration} minutes\n"
            )

            if task.get('description'):
                message += f"\n{task['description']}\n"

            if task.get('ai_reasoning'):
                message += f"\n💡 _{task['ai_reasoning']}_\n"

            # Add quick action buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Mark Done", callback_data=f"complete_task_{task['id']}"),
                    InlineKeyboardButton("⏭️ Skip", callback_data=f"skip_task_{task['id']}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send message
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

            logger.info(f"Sent task reminder to user {user_id} for task {task['id']}")
            return True

        except Exception as e:
            logger.error(f"Error sending task reminder: {e}")
            return False

    async def send_daily_summary(
        self,
        user_id: int,
        tasks: List[Dict[str, Any]],
        summary_date: date
    ) -> bool:
        """
        Send daily task summary.

        Args:
            user_id: Telegram user ID
            tasks: List of tasks for the day
            summary_date: Date for the summary

        Returns:
            True if sent successfully
        """
        try:
            if not tasks:
                # No tasks for the day
                message = (
                    f"🌅 *Good Morning!*\n\n"
                    f"You have no scheduled tasks for today.\n"
                    f"Enjoy your free time! 😊"
                )
            else:
                date_str = summary_date.strftime("%A, %B %d")

                message = (
                    f"🌅 *Good Morning!*\n\n"
                    f"Here's your plan for {date_str}:\n\n"
                )

                for i, task in enumerate(tasks[:10], 1):  # Limit to 10 tasks
                    time_str = task.get('scheduled_time', '')[:5] if task.get('scheduled_time') else 'All day'
                    title = task['title']

                    message += f"{i}. {time_str} - {title}\n"

                if len(tasks) > 10:
                    message += f"\n...and {len(tasks) - 10} more tasks\n"

                message += f"\n📊 Total: {len(tasks)} tasks\n"
                message += "\nYou've got this! 💪\n\n"
                message += "View details: /today"

            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )

            logger.info(f"Sent daily summary to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False

    async def send_weekly_summary(
        self,
        user_id: int,
        stats: Dict[str, Any]
    ) -> bool:
        """
        Send weekly progress summary.

        Args:
            user_id: Telegram user ID
            stats: Statistics dictionary

        Returns:
            True if sent successfully
        """
        try:
            completed = stats.get('completed', 0)
            pending = stats.get('pending', 0)
            skipped = stats.get('skipped', 0)
            total = completed + pending + skipped

            completion_rate = (completed / total * 100) if total > 0 else 0

            message = (
                f"📊 *Weekly Progress Report*\n\n"
                f"✅ Completed: {completed}\n"
                f"📝 Pending: {pending}\n"
                f"⏭️ Skipped: {skipped}\n\n"
                f"📈 Completion Rate: {completion_rate:.1f}%\n\n"
            )

            if completion_rate >= 80:
                message += "🌟 Excellent work this week! Keep it up!\n"
            elif completion_rate >= 60:
                message += "👍 Good progress! You're on track.\n"
            elif completion_rate >= 40:
                message += "💪 Keep pushing! You can do better.\n"
            else:
                message += "🔄 Consider adjusting your plan with /plan\n"

            message += "\nView your plan: /week"

            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )

            logger.info(f"Sent weekly summary to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending weekly summary: {e}")
            return False

    async def send_custom_message(
        self,
        user_id: int,
        message: str,
        parse_mode: str = 'Markdown'
    ) -> bool:
        """
        Send a custom message to a user.

        Args:
            user_id: Telegram user ID
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)

        Returns:
            True if sent successfully
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode
            )

            logger.info(f"Sent custom message to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending custom message: {e}")
            return False

    async def send_goal_milestone(
        self,
        user_id: int,
        goal_title: str,
        milestone_message: str
    ) -> bool:
        """
        Send a goal milestone notification.

        Args:
            user_id: Telegram user ID
            goal_title: Goal title
            milestone_message: Milestone description

        Returns:
            True if sent successfully
        """
        try:
            message = (
                f"🎯 *Goal Milestone Reached!*\n\n"
                f"*{goal_title}*\n\n"
                f"{milestone_message}\n\n"
                f"Great progress! 🎉"
            )

            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )

            logger.info(f"Sent milestone notification to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending milestone notification: {e}")
            return False
