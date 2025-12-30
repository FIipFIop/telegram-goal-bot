"""
Error handling utilities for the Telegram bot.
Provides centralized error handling and logging.
"""

from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps
import logging
import traceback

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler for the bot.
    Logs errors and sends user-friendly messages.

    Args:
        update: Telegram update object (may be None)
        context: Callback context containing error
    """
    try:
        # Log the error
        logger.error("Exception while handling an update:", exc_info=context.error)

        # Get error traceback
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)

        # Log detailed traceback
        logger.error(f"Traceback:\n{tb_string}")

        # Send message to user if update is available
        if update and hasattr(update, 'effective_message') and update.effective_message:
            try:
                error_message = (
                    "❌ An error occurred while processing your request.\n\n"
                    "Please try again. If the problem persists, use /start to restart the bot."
                )

                await update.effective_message.reply_text(error_message)

            except Exception as e:
                logger.error(f"Failed to send error message to user: {e}")

    except Exception as e:
        logger.error(f"Error in error_handler: {e}")


def handle_errors(func):
    """
    Decorator to handle errors in handler functions.
    Catches exceptions and sends user-friendly error messages.

    Args:
        func: Async function to wrap

    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)

            # Try to send error message to user
            try:
                if update and hasattr(update, 'effective_message') and update.effective_message:
                    await update.effective_message.reply_text(
                        "❌ An error occurred while processing your request.\n\n"
                        "Please try again or use /help for assistance."
                    )
                elif update and hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.answer(
                        "An error occurred. Please try again.",
                        show_alert=True
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")

            # Re-raise in development, swallow in production
            # This prevents the bot from crashing
            return None

    return wrapper


def handle_repository_errors(func):
    """
    Decorator specifically for repository methods.
    Logs errors and returns None on failure.

    Args:
        func: Async function to wrap

    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Repository error in {func.__name__}: {e}", exc_info=True)
            return None

    return wrapper


class BotError(Exception):
    """Base exception for bot errors."""
    pass


class ValidationError(BotError):
    """Raised when input validation fails."""
    pass


class DatabaseError(BotError):
    """Raised when database operations fail."""
    pass


class AIServiceError(BotError):
    """Raised when AI service fails."""
    pass


class ScheduleConflictError(BotError):
    """Raised when there's a schedule conflict."""
    pass
