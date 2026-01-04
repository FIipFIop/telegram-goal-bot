"""
Cron endpoint to send daily summaries at 7 AM.
Runs once daily via Vercel Cron.
"""

from telegram import Bot
from datetime import date
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from database.repositories.user_repository import UserRepository
from database.repositories.task_repository import TaskRepository


async def handler(request):
    """Send daily summaries to all active users."""
    try:
        user_repo = UserRepository()
        task_repo = TaskRepository()
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        await bot.initialize()

        # Get all active users
        users = await user_repo.get_all_active_users()

        sent_count = 0
        for user in users:
            try:
                # Get today's tasks
                today = date.today()
                tasks = await task_repo.get_tasks_by_date(user['user_id'], today)

                if tasks:
                    # Build summary message
                    message = f"🌅 *Good Morning!*\n\n"
                    message += f"You have *{len(tasks)} tasks* scheduled for today:\n\n"

                    for i, task in enumerate(tasks[:10], 1):
                        time_str = task.get('scheduled_time', '')[:5] if task.get('scheduled_time') else 'Anytime'
                        message += f"{i}. {task['title']}\n"
                        message += f"   🕐 {time_str}\n\n"

                    if len(tasks) > 10:
                        message += f"...and {len(tasks) - 10} more\n\n"

                    message += "Use /today to view and manage your tasks!\n"
                    message += "Have a productive day! 💪"

                    await bot.send_message(
                        chat_id=user['user_id'],
                        text=message,
                        parse_mode='Markdown'
                    )

                    sent_count += 1

            except Exception as e:
                print(f"Error sending daily summary to user {user['user_id']}: {e}")

        await bot.shutdown()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "summaries_sent": sent_count
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }


# Vercel entry point
def vercel_handler(request):
    """Synchronous wrapper for Vercel."""
    import asyncio
    return asyncio.run(handler(request))
