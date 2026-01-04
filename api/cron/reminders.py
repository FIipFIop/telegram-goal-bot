"""
Cron endpoint to check and send pending reminders.
Runs every minute via Vercel Cron (paid feature) or external cron service.
"""

from telegram import Bot
from datetime import datetime, timezone
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from database.repositories.reminder_repository import ReminderRepository
from database.repositories.task_repository import TaskRepository


async def handler(request):
    """Check and send pending reminders."""
    try:
        # Verify cron secret (optional security)
        auth_header = request.headers.get('authorization', '')
        # if auth_header != f"Bearer {settings.CRON_SECRET}":
        #     return {"statusCode": 401, "body": "Unauthorized"}

        reminder_repo = ReminderRepository()
        task_repo = TaskRepository()
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        await bot.initialize()

        # Get pending reminders
        now = datetime.now(timezone.utc)
        reminders = await reminder_repo.get_pending_reminders(before_time=now, limit=50)

        sent_count = 0
        for reminder in reminders:
            try:
                # Get task details
                task = await task_repo.get_task(reminder['task_id'])

                if task:
                    # Send reminder
                    message = f"⏰ *Reminder*\n\n{reminder['message']}"

                    await bot.send_message(
                        chat_id=reminder['user_id'],
                        text=message,
                        parse_mode='Markdown'
                    )

                    # Mark as sent
                    await reminder_repo.mark_reminder_sent(reminder['id'])
                    sent_count += 1

            except Exception as e:
                print(f"Error sending reminder {reminder['id']}: {e}")
                await reminder_repo.mark_reminder_failed(reminder['id'])

        await bot.shutdown()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "reminders_sent": sent_count
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
