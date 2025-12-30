"""
Start and help command handlers for the Telegram bot.
Handles initial user interaction and help information.
"""

from telegram import Update
from telegram.ext import ContextTypes
from database.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    Creates or retrieves user and sends welcome message.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    user = update.effective_user
    chat_id = update.effective_chat.id

    try:
        # Initialize user repository
        user_repo = UserRepository()

        # Get or create user in database
        db_user = await user_repo.get_or_create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

        if db_user:
            # Send welcome message
            welcome_message = (
                f"Welcome{' ' + user.first_name if user.first_name else ''} to the Goal Planning Bot!\n\n"
                "I'll help you achieve your yearly goals by:\n"
                "- Breaking them down into manageable daily tasks\n"
                "- Asking clarifying questions to understand your goals better\n"
                "- Creating an optimized plan that fits your schedule\n"
                "- Sending you daily reminders to stay on track\n\n"
                "Let's get started! Here's what you can do:\n\n"
                "📅 /schedule - Set your weekly availability (school, sports, etc.)\n"
                "🎯 /newgoal - Add a new goal for the year\n"
                "📌 /newevent - Add special one-time events\n"
                "📋 /plan - Generate your personalized action plan\n"
                "📊 /goals - View and manage your goals\n"
                "❓ /help - Show this help message\n\n"
                "Start by setting your schedule with /schedule, then add your goals!"
            )

            await update.message.reply_text(welcome_message)
            logger.info(f"User {user.id} started the bot")

        else:
            await update.message.reply_text(
                "Sorry, there was an error setting up your account. Please try again later."
            )
            logger.error(f"Failed to create user {user.id}")

    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "An error occurred. Please try again later."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command.
    Shows available commands and usage information.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    try:
        help_message = (
            "📖 Goal Planning Bot - Help\n\n"
            "Available Commands:\n\n"
            "🎯 Goal Management:\n"
            "/newgoal - Create a new goal (I'll ask questions to help clarify)\n"
            "/goals - View all your goals\n"
            "/deletegoal - Remove a goal\n\n"
            "📅 Schedule Management:\n"
            "/schedule - Set up your weekly availability\n"
            "/viewschedule - See your current schedule\n"
            "/newevent - Add a special one-time event\n"
            "/events - View and manage your events\n\n"
            "📋 Planning:\n"
            "/plan - Generate AI-powered action plan\n"
            "/today - View today's tasks\n"
            "/week - View this week's tasks\n"
            "/complete - Mark a task as complete\n\n"
            "⚙️ Settings:\n"
            "/timezone - Set your timezone\n"
            "/settings - View and update your settings\n\n"
            "ℹ️ Other:\n"
            "/start - Restart the bot\n"
            "/help - Show this help message\n\n"
            "How it works:\n"
            "1️⃣ Set your weekly schedule (when you're busy with school, sports, etc.)\n"
            "2️⃣ Add your yearly goals\n"
            "3️⃣ I'll ask clarifying questions to understand your goals better\n"
            "4️⃣ Generate your personalized plan with /plan\n"
            "5️⃣ Receive daily reminders and track your progress!\n\n"
            "Need help? Just type your question and I'll do my best to assist!"
        )

        await update.message.reply_text(help_message)
        logger.info(f"User {update.effective_user.id} requested help")

    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await update.message.reply_text(
            "An error occurred while displaying help. Please try again."
        )
