"""
Event command handlers for viewing and managing special events.
Provides commands to view, delete, and manage user's special events.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.repositories.event_repository import EventRepository
from database.repositories.user_repository import UserRepository
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /events command - show all user's events.

    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        user_repo = UserRepository()
        event_repo = EventRepository()

        # Ensure user exists
        await user_repo.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name
        )

        # Get upcoming events
        upcoming_events = await event_repo.get_upcoming_events(user_id, limit=20)

        if not upcoming_events:
            await update.message.reply_text(
                "📅 *Your Events*\n\n"
                "You don't have any upcoming events.\n\n"
                "Use /newevent to add a special event.",
                parse_mode='Markdown'
            )
            return

        # Format events list
        message = "📅 *Your Upcoming Events*\n\n"

        for event in upcoming_events[:10]:  # Limit to 10 for display
            event_date = date.fromisoformat(event['event_date'])
            date_str = event_date.strftime('%b %d, %Y')

            if event.get('is_all_day'):
                time_str = "All day"
            else:
                start = event.get('start_time', '')[:5]
                end = event.get('end_time', '')[:5]
                time_str = f"{start} - {end}"

            message += f"• *{event['title']}*\n"
            message += f"  📅 {date_str}\n"
            message += f"  🕐 {time_str}\n"

            if event.get('description'):
                desc = event['description'][:50]
                if len(event['description']) > 50:
                    desc += "..."
                message += f"  📝 {desc}\n"

            message += "\n"

        if len(upcoming_events) > 10:
            message += f"...and {len(upcoming_events) - 10} more events\n\n"

        message += "Tap an event below to manage it:"

        # Create keyboard with event options
        keyboard = []
        for event in upcoming_events[:5]:  # Show buttons for first 5
            title = event['title'][:30]
            if len(event['title']) > 30:
                title += "..."
            keyboard.append([
                InlineKeyboardButton(
                    title,
                    callback_data=f"event_view_{event['id']}"
                )
            ])

        keyboard.append([InlineKeyboardButton("➕ Add New Event", callback_data="event_add_new")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error in events_command: {e}")
        await update.message.reply_text(
            "An error occurred while retrieving your events. Please try again."
        )


async def handle_event_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle event view callback."""
    try:
        query = update.callback_query
        await query.answer()

        event_id = query.data.replace("event_view_", "")
        event_repo = EventRepository()

        event = await event_repo.get_event(event_id)

        if not event:
            await query.edit_message_text("Event not found.")
            return

        # Format event details
        event_date = date.fromisoformat(event['event_date'])
        date_str = event_date.strftime('%A, %B %d, %Y')

        message = (
            f"📅 *{event['title']}*\n\n"
            f"*Date:* {date_str}\n"
        )

        if event.get('is_all_day'):
            message += "*Time:* All day\n"
        else:
            start = event.get('start_time', '')[:5]
            end = event.get('end_time', '')[:5]
            message += f"*Time:* {start} - {end}\n"

        if event.get('description'):
            message += f"\n*Description:*\n{event['description']}\n"

        # Action buttons
        keyboard = [
            [InlineKeyboardButton("🗑️ Delete Event", callback_data=f"event_delete_{event_id}")],
            [InlineKeyboardButton("« Back to Events", callback_data="event_back_to_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error in handle_event_view: {e}")
        await query.message.reply_text("An error occurred. Please try again.")


async def handle_event_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle event deletion callback."""
    try:
        query = update.callback_query
        await query.answer()

        event_id = query.data.replace("event_delete_", "")
        event_repo = EventRepository()

        # Get event title before deletion
        event = await event_repo.get_event(event_id)

        if not event:
            await query.edit_message_text("Event not found.")
            return

        # Delete event
        success = await event_repo.delete_event(event_id)

        if success:
            await query.edit_message_text(
                f"✅ Event '{event['title']}' has been deleted.\n\n"
                "Use /events to view your remaining events."
            )
        else:
            await query.edit_message_text(
                "❌ Failed to delete event. Please try again."
            )

    except Exception as e:
        logger.error(f"Error in handle_event_delete: {e}")
        await query.message.reply_text("An error occurred. Please try again.")


async def handle_event_add_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle add new event callback."""
    try:
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "To add a new event, please use the /newevent command."
        )

    except Exception as e:
        logger.error(f"Error in handle_event_add_new: {e}")
        await query.message.reply_text("An error occurred. Please try again.")


async def handle_event_back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle back to events list callback."""
    try:
        query = update.callback_query
        await query.answer()

        # Re-trigger events command
        await events_command(update, context)

    except Exception as e:
        logger.error(f"Error in handle_event_back_to_list: {e}")
        await query.message.reply_text("An error occurred. Please try again.")


def get_event_callback_handlers():
    """
    Get list of callback handlers for event management.

    Returns:
        List of CallbackQueryHandler instances
    """
    return [
        CallbackQueryHandler(handle_event_view, pattern="^event_view_"),
        CallbackQueryHandler(handle_event_delete, pattern="^event_delete_"),
        CallbackQueryHandler(handle_event_add_new, pattern="^event_add_new$"),
        CallbackQueryHandler(handle_event_back_to_list, pattern="^event_back_to_list$")
    ]
