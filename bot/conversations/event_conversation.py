"""
Event conversation handler for creating special events.
Handles multi-turn conversation for adding one-time events.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from database.repositories.event_repository import EventRepository
from database.repositories.user_repository import UserRepository
from utils.validators import validate_time_format, validate_date_format, validate_time_range
from datetime import date, time
import logging

logger = logging.getLogger(__name__)

# Conversation states
TITLE, EVENT_DATE, EVENT_TYPE, START_TIME, END_TIME, DESCRIPTION, CONFIRM = range(7)


async def newevent_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the new event conversation."""
    try:
        await update.message.reply_text(
            "📅 *Create New Special Event*\n\n"
            "Let's add a special event to your calendar. "
            "This will block off time in your schedule.\n\n"
            "First, what's the event title?\n\n"
            "_(e.g., 'Doctor Appointment', 'Birthday Party', 'Conference')_\n\n"
            "Type /cancel to cancel.",
            parse_mode='Markdown'
        )
        return TITLE

    except Exception as e:
        logger.error(f"Error in newevent_start: {e}")
        await update.message.reply_text(
            "An error occurred. Please try again with /newevent"
        )
        return ConversationHandler.END


async def event_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle event title input."""
    try:
        title = update.message.text.strip()

        if len(title) < 3:
            await update.message.reply_text(
                "Event title is too short. Please provide at least 3 characters."
            )
            return TITLE

        if len(title) > 200:
            await update.message.reply_text(
                "Event title is too long. Please keep it under 200 characters."
            )
            return TITLE

        # Store title
        context.user_data['event_title'] = title

        await update.message.reply_text(
            f"Great! Event: *{title}*\n\n"
            "When is this event?\n"
            "Please provide the date in YYYY-MM-DD format.\n\n"
            "_(e.g., 2025-01-15 for January 15, 2025)_",
            parse_mode='Markdown'
        )
        return EVENT_DATE

    except Exception as e:
        logger.error(f"Error in event_title: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return TITLE


async def event_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle event date input."""
    try:
        date_str = update.message.text.strip()

        # Validate date format
        is_valid, parsed_date, error = validate_date_format(date_str)

        if not is_valid:
            await update.message.reply_text(
                f"❌ {error}\n\n"
                "Please provide the date in YYYY-MM-DD format.\n"
                "_(e.g., 2025-01-15)_",
                parse_mode='Markdown'
            )
            return EVENT_DATE

        # Check if date is in the past
        if parsed_date < date.today():
            await update.message.reply_text(
                "❌ The event date cannot be in the past.\n\n"
                "Please provide a future date."
            )
            return EVENT_DATE

        # Store date
        context.user_data['event_date'] = parsed_date

        # Ask for event type
        keyboard = [
            [InlineKeyboardButton("All Day Event", callback_data="event_type_allday")],
            [InlineKeyboardButton("Specific Time", callback_data="event_type_timed")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"Date set: *{parsed_date.strftime('%A, %B %d, %Y')}*\n\n"
            "Is this an all-day event or does it have specific times?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return EVENT_TYPE

    except Exception as e:
        logger.error(f"Error in event_date_input: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return EVENT_DATE


async def event_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle event type selection."""
    try:
        query = update.callback_query
        await query.answer()

        event_type = query.data.replace("event_type_", "")

        if event_type == "allday":
            # All-day event - skip to description
            context.user_data['is_all_day'] = True
            context.user_data['start_time'] = None
            context.user_data['end_time'] = None

            await query.edit_message_text(
                "✅ All-day event selected\n\n"
                "Would you like to add a description? (Optional)\n\n"
                "Type your description or type 'skip' to skip.",
                parse_mode='Markdown'
            )
            return DESCRIPTION

        else:
            # Timed event - ask for start time
            context.user_data['is_all_day'] = False

            await query.edit_message_text(
                "What time does the event start?\n\n"
                "Please provide the time in 24-hour format (HH:MM).\n"
                "_(e.g., 14:30 for 2:30 PM)_",
                parse_mode='Markdown'
            )
            return START_TIME

    except Exception as e:
        logger.error(f"Error in event_type: {e}")
        await query.message.reply_text("An error occurred. Please try again.")
        return EVENT_TYPE


async def event_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle event start time input."""
    try:
        time_str = update.message.text.strip()

        # Validate time format
        is_valid, parsed_time, error = validate_time_format(time_str)

        if not is_valid:
            await update.message.reply_text(
                f"❌ {error}\n\n"
                "Please provide the time in HH:MM format.\n"
                "_(e.g., 14:30)_",
                parse_mode='Markdown'
            )
            return START_TIME

        # Store start time
        context.user_data['start_time'] = parsed_time

        await update.message.reply_text(
            f"Start time set: *{parsed_time.strftime('%H:%M')}*\n\n"
            "What time does the event end?\n\n"
            "Please provide the end time in HH:MM format.",
            parse_mode='Markdown'
        )
        return END_TIME

    except Exception as e:
        logger.error(f"Error in event_start_time: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return START_TIME


async def event_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle event end time input."""
    try:
        time_str = update.message.text.strip()

        # Validate time format
        is_valid, parsed_time, error = validate_time_format(time_str)

        if not is_valid:
            await update.message.reply_text(
                f"❌ {error}\n\n"
                "Please provide the time in HH:MM format.\n"
                "_(e.g., 16:00)_",
                parse_mode='Markdown'
            )
            return END_TIME

        # Validate time range
        start_time = context.user_data['start_time']
        is_valid_range, range_error = validate_time_range(start_time, parsed_time)

        if not is_valid_range:
            await update.message.reply_text(
                f"❌ {range_error}\n\n"
                "Please provide an end time that is after the start time."
            )
            return END_TIME

        # Store end time
        context.user_data['end_time'] = parsed_time

        # Check for conflicts
        event_repo = EventRepository()
        user_id = update.effective_user.id
        event_date = context.user_data['event_date']

        has_conflict = await event_repo.check_event_conflict(
            user_id=user_id,
            event_date=event_date,
            start_time=start_time,
            end_time=parsed_time
        )

        if has_conflict:
            await update.message.reply_text(
                "⚠️ *Warning:* This event conflicts with another event on the same day.\n\n"
                "You can still continue, but the times will overlap.",
                parse_mode='Markdown'
            )

        await update.message.reply_text(
            f"End time set: *{parsed_time.strftime('%H:%M')}*\n\n"
            "Would you like to add a description? (Optional)\n\n"
            "Type your description or type 'skip' to skip.",
            parse_mode='Markdown'
        )
        return DESCRIPTION

    except Exception as e:
        logger.error(f"Error in event_end_time: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return END_TIME


async def event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle event description input."""
    try:
        description = update.message.text.strip()

        if description.lower() == 'skip':
            context.user_data['event_description'] = None
        else:
            if len(description) > 500:
                await update.message.reply_text(
                    "Description is too long. Please keep it under 500 characters."
                )
                return DESCRIPTION
            context.user_data['event_description'] = description

        # Show confirmation
        await show_event_confirmation(update, context)
        return CONFIRM

    except Exception as e:
        logger.error(f"Error in event_description: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return DESCRIPTION


async def show_event_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show event confirmation summary."""
    title = context.user_data['event_title']
    event_date = context.user_data['event_date']
    is_all_day = context.user_data['is_all_day']
    start_time = context.user_data.get('start_time')
    end_time = context.user_data.get('end_time')
    description = context.user_data.get('event_description')

    # Format summary
    summary = (
        "📅 *Event Summary*\n\n"
        f"*Title:* {title}\n"
        f"*Date:* {event_date.strftime('%A, %B %d, %Y')}\n"
    )

    if is_all_day:
        summary += "*Time:* All day\n"
    else:
        summary += f"*Time:* {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"

    if description:
        summary += f"*Description:* {description}\n"

    summary += "\nIs this correct?"

    # Confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="event_confirm_yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="event_confirm_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        summary,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def event_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle event confirmation."""
    try:
        query = update.callback_query
        await query.answer()

        if query.data == "event_confirm_no":
            await query.edit_message_text(
                "❌ Event creation cancelled.\n\n"
                "Use /newevent to start again."
            )
            context.user_data.clear()
            return ConversationHandler.END

        # Create the event
        event_repo = EventRepository()
        user_repo = UserRepository()

        user_id = update.effective_user.id

        # Ensure user exists
        await user_repo.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name
        )

        # Create event
        event = await event_repo.create_event(
            user_id=user_id,
            title=context.user_data['event_title'],
            event_date=context.user_data['event_date'],
            start_time=context.user_data.get('start_time'),
            end_time=context.user_data.get('end_time'),
            description=context.user_data.get('event_description'),
            is_all_day=context.user_data['is_all_day']
        )

        if event:
            await query.edit_message_text(
                "✅ *Event created successfully!*\n\n"
                "This event will be considered when generating your task plans.\n\n"
                "Use /events to view all your events.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Failed to create event. Please try again with /newevent"
            )

        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error in event_confirm: {e}")
        await query.message.reply_text(
            "An error occurred while creating the event. Please try again."
        )
        context.user_data.clear()
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "Event creation cancelled. Use /newevent to start again."
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_event_conversation_handler() -> ConversationHandler:
    """
    Create and return the event conversation handler.

    Returns:
        ConversationHandler for event creation
    """
    return ConversationHandler(
        entry_points=[CommandHandler("newevent", newevent_start)],
        states={
            TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, event_title)
            ],
            EVENT_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, event_date_input)
            ],
            EVENT_TYPE: [
                CallbackQueryHandler(event_type, pattern="^event_type_")
            ],
            START_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, event_start_time)
            ],
            END_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, event_end_time)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, event_description)
            ],
            CONFIRM: [
                CallbackQueryHandler(event_confirm, pattern="^event_confirm_")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=300  # 5 minutes timeout
    )
