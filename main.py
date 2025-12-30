"""
Main entry point for the Telegram Goal Planning Bot.
Initializes and runs the bot with all command handlers.
"""

import asyncio
import logging
from telegram.ext import Application, CommandHandler
from config import settings
from bot.handlers import start, goals, schedule, plan, events
from bot.conversations.goal_conversation import get_goal_conversation_handler
from bot.conversations.schedule_conversation import get_schedule_conversation_handler
from bot.conversations.event_conversation import get_event_conversation_handler
from services.scheduler_service import SchedulerService
from utils.error_handler import error_handler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Main function to initialize and run the Telegram bot.
    Sets up command handlers and starts polling.
    """
    logger.info("Starting Telegram Goal Planning Bot...")

    try:
        # Create application instance
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # Add command handlers
        logger.info("Registering command handlers...")
        application.add_handler(CommandHandler("start", start.start_command))
        application.add_handler(CommandHandler("help", start.help_command))

        # Phase 2: Goal Management
        logger.info("Registering goal handlers...")
        application.add_handler(get_goal_conversation_handler())  # /newgoal conversation
        application.add_handler(CommandHandler("goals", goals.goals_command))

        # Add goal callback handlers
        for handler in goals.get_goal_callback_handlers():
            application.add_handler(handler)

        # Phase 3: Schedule Management
        logger.info("Registering schedule handlers...")
        application.add_handler(get_schedule_conversation_handler())  # /schedule conversation
        application.add_handler(CommandHandler("viewschedule", schedule.viewschedule_command))

        # Add schedule callback handlers
        for handler in schedule.get_schedule_callback_handlers():
            application.add_handler(handler)

        # Phase 6: Special Events
        logger.info("Registering event handlers...")
        application.add_handler(get_event_conversation_handler())  # /newevent conversation
        application.add_handler(CommandHandler("events", events.events_command))

        # Add event callback handlers
        for handler in events.get_event_callback_handlers():
            application.add_handler(handler)

        # Phase 4: AI-Powered Planning
        logger.info("Registering plan handlers...")
        application.add_handler(CommandHandler("plan", plan.plan_command))
        application.add_handler(CommandHandler("today", plan.today_command))
        application.add_handler(CommandHandler("week", plan.week_command))

        # Add plan callback handlers
        for handler in plan.get_plan_callback_handlers():
            application.add_handler(handler)

        # Register global error handler
        application.add_error_handler(error_handler)

        logger.info("Bot initialized successfully")

        # Start the bot
        logger.info("Starting bot polling...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=["message", "callback_query"]
        )

        # Phase 5: Start Reminder Scheduler
        logger.info("Starting reminder scheduler...")
        scheduler = SchedulerService(application.bot)
        await scheduler.start()

        logger.info("Bot is running. Press Ctrl+C to stop.")

        # Keep the bot running
        await asyncio.Event().wait()

    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise
    finally:
        if 'scheduler' in locals():
            await scheduler.stop()
        if 'application' in locals():
            await application.stop()
            logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
