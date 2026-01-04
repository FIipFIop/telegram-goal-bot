"""
Cron endpoint to send weekly summaries on Sundays.
Runs once weekly via Vercel Cron.
"""

from telegram import Bot
from datetime import date, timedelta
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from database.repositories.user_repository import UserRepository
from database.repositories.task_repository import TaskRepository


async def handler(request):
    """Send weekly summaries to all active users."""
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
                # Get this week's tasks
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)

                all_tasks = []
                current_date = week_start
                while current_date <= week_end:
                    tasks = await task_repo.get_tasks_by_date(user['user_id'], current_date)
                    all_tasks.extend(tasks)
                    current_date += timedelta(days=1)

                if all_tasks:
                    # Calculate statistics
                    total = len(all_tasks)
                    completed = len([t for t in all_tasks if t['status'] == 'completed'])
                    completion_rate = int((completed / total) * 100) if total > 0 else 0

                    # Build summary message
                    message = f"📊 *Weekly Progress Report*\n\n"
                    message += f"*This Week's Stats:*\n"
                    message += f"✅ Completed: {completed}/{total} tasks\n"
                    message += f"📈 Completion Rate: {completion_rate}%\n\n"

                    if completion_rate >= 80:
                        message += "🎉 Excellent work! Keep it up!\n"
                    elif completion_rate >= 50:
                        message += "👍 Good progress! You're on track!\n"
                    else:
                        message += "💪 Let's aim higher next week!\n"

                    message += "\nUse /week to review your weekly tasks."

                    await bot.send_message(
                        chat_id=user['user_id'],
                        text=message,
                        parse_mode='Markdown'
                    )

                    sent_count += 1

            except Exception as e:
                print(f"Error sending weekly summary to user {user['user_id']}: {e}")

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
