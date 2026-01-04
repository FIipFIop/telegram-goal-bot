"""
Vercel serverless function to handle Telegram webhook updates.
This replaces the polling mechanism with webhook-based updates.
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from bot.handlers import start, goals, schedule, plan, events
from bot.conversations.goal_conversation import get_goal_conversation_handler
from bot.conversations.schedule_conversation import get_schedule_conversation_handler
from bot.conversations.event_conversation import get_event_conversation_handler
from utils.error_handler import error_handler


# Initialize application once (cached between invocations)
application = None


def get_application():
    """Get or create the bot application."""
    global application

    if application is None:
        # Create application
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # Register handlers
        application.add_handler(CommandHandler("start", start.start_command))
        application.add_handler(CommandHandler("help", start.help_command))

        # Goal handlers
        application.add_handler(get_goal_conversation_handler())
        application.add_handler(CommandHandler("goals", goals.goals_command))
        for handler in goals.get_goal_callback_handlers():
            application.add_handler(handler)

        # Schedule handlers
        application.add_handler(get_schedule_conversation_handler())
        application.add_handler(CommandHandler("viewschedule", schedule.viewschedule_command))
        for handler in schedule.get_schedule_callback_handlers():
            application.add_handler(handler)

        # Event handlers
        application.add_handler(get_event_conversation_handler())
        application.add_handler(CommandHandler("events", events.events_command))
        for handler in events.get_event_callback_handlers():
            application.add_handler(handler)

        # Plan handlers
        application.add_handler(CommandHandler("plan", plan.plan_command))
        application.add_handler(CommandHandler("today", plan.today_command))
        application.add_handler(CommandHandler("week", plan.week_command))
        for handler in plan.get_plan_callback_handlers():
            application.add_handler(handler)

        # Error handler
        application.add_error_handler(error_handler)

    return application


async def handler(request):
    """
    Vercel serverless function handler.

    Args:
        request: HTTP request object

    Returns:
        HTTP response
    """
    try:
        # Get request body
        if request.method == "POST":
            body = await request.json()
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "Bot is running"})
            }

        # Get application
        app = get_application()

        # Initialize app if not initialized
        if not app.bot._initialized:
            await app.initialize()

        # Create Update object from request
        update = Update.de_json(body, app.bot)

        # Process update
        await app.process_update(update)

        return {
            "statusCode": 200,
            "body": json.dumps({"status": "ok"})
        }

    except Exception as e:
        print(f"Error processing update: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# Vercel entry point
def vercel_handler(request):
    """Synchronous wrapper for Vercel."""
    import asyncio
    return asyncio.run(handler(request))
