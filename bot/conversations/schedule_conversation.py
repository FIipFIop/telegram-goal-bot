"""
Schedule conversation handler for setting up weekly availability.
Guides users through adding recurring time blocks to their schedule.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from database.repositories.schedule_repository import ScheduleRepository
from utils.validators import (
    validate_time_format,
    validate_time_range,
    get_day_name,
    format_time_24h
)
from bot.keyboards import (
    build_day_selection_keyboard,
    build_activity_type_keyboard,
    build_add_more_blocks_keyboard
)
import logging

logger = logging.getLogger(__name__)

# Conversation states
DAY_SELECTION, START_TIME, END_TIME, ACTIVITY_TYPE, DESCRIPTION, ADD_MORE = range(6)


async def start_schedule_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the schedule setup conversation.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    # Initialize conversation data
    context.user_data['schedule_block'] = {}

    keyboard = build_day_selection_keyboard()

    await update.message.reply_text(
        "Let's set up your weekly schedule!\n\n"
        "This helps me avoid scheduling tasks during your busy times like school, sports, work, etc.\n\n"
        "First, which day of the week is this for?\n\n"
        "Send /cancel anytime to stop.",
        reply_markup=keyboard
    )

    return DAY_SELECTION


async def receive_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive day selection and ask for start time.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    query = update.callback_query
    await query.answer()

    # Extract day number from callback data
    day_of_week = int(query.data.replace("day_", ""))
    context.user_data['schedule_block']['day_of_week'] = day_of_week

    day_name = get_day_name(day_of_week)

    await query.edit_message_text(
        f"✓ Day: *{day_name}*\n\n"
        "What time does this activity start?\n\n"
        "Please send the start time in 24-hour format (HH:MM)\n"
        "Examples: 09:00, 14:30, 18:00\n\n"
        "You can also use 12-hour format: 9:00 AM, 2:30 PM",
        parse_mode='Markdown'
    )

    return START_TIME


async def receive_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive and validate start time.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    time_str = update.message.text.strip()

    # Validate time format
    is_valid, start_time, error = validate_time_format(time_str)

    if not is_valid:
        await update.message.reply_text(
            f"{error}\n"
            "Examples: 09:00, 14:30, 6:00 PM\n\n"
            "Try again:"
        )
        return START_TIME

    # Store start time
    context.user_data['schedule_block']['start_time'] = start_time

    await update.message.reply_text(
        f"✓ Start time: {format_time_24h(start_time)}\n\n"
        "What time does this activity end?\n\n"
        "Please send the end time (HH:MM):"
    )

    return END_TIME


async def receive_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive and validate end time.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    time_str = update.message.text.strip()

    # Validate time format
    is_valid, end_time, error = validate_time_format(time_str)

    if not is_valid:
        await update.message.reply_text(
            f"{error}\n"
            "Examples: 17:00, 20:30, 11:00 PM\n\n"
            "Try again:"
        )
        return END_TIME

    # Validate time range
    start_time = context.user_data['schedule_block']['start_time']
    is_valid_range, range_error = validate_time_range(start_time, end_time)

    if not is_valid_range:
        await update.message.reply_text(
            f"{range_error}\n\n"
            f"Your start time is: {format_time_24h(start_time)}\n"
            "Please enter a later end time:"
        )
        return END_TIME

    # Check for overlaps
    user = update.effective_user
    day_of_week = context.user_data['schedule_block']['day_of_week']

    schedule_repo = ScheduleRepository()
    has_overlap = await schedule_repo.check_overlap(
        user_id=user.id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time
    )

    if has_overlap:
        day_name = get_day_name(day_of_week)
        await update.message.reply_text(
            f"⚠️ This time overlaps with an existing block on {day_name}!\n\n"
            "Please choose a different time or delete the existing block first.\n\n"
            "Enter a different end time:"
        )
        return END_TIME

    # Store end time
    context.user_data['schedule_block']['end_time'] = end_time

    keyboard = build_activity_type_keyboard()

    await update.message.reply_text(
        f"✓ End time: {format_time_24h(end_time)}\n\n"
        "What type of activity is this?",
        reply_markup=keyboard
    )

    return ACTIVITY_TYPE


async def receive_activity_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive activity type selection.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    query = update.callback_query
    await query.answer()

    # Extract activity type from callback data
    activity_type = query.data.replace("activity_", "")
    context.user_data['schedule_block']['activity_type'] = activity_type

    await query.edit_message_text(
        f"✓ Activity: {activity_type.title()}\n\n"
        "Would you like to add a description? (Optional)\n\n"
        "Send a description or type 'skip' to continue."
    )

    return DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive optional description and save schedule block.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    description = update.message.text.strip()

    if description.lower() != 'skip':
        context.user_data['schedule_block']['description'] = description
    else:
        context.user_data['schedule_block']['description'] = None

    # Save to database
    try:
        user = update.effective_user
        block_data = context.user_data['schedule_block']

        schedule_repo = ScheduleRepository()
        saved_block = await schedule_repo.create_time_block(
            user_id=user.id,
            day_of_week=block_data['day_of_week'],
            start_time=block_data['start_time'],
            end_time=block_data['end_time'],
            activity_type=block_data['activity_type'],
            description=block_data.get('description')
        )

        if saved_block:
            # Format summary
            day_name = get_day_name(block_data['day_of_week'])
            start_str = format_time_24h(block_data['start_time'])
            end_str = format_time_24h(block_data['end_time'])

            summary = (
                "✅ *Schedule block added!*\n\n"
                f"📅 {day_name}\n"
                f"🕐 {start_str} - {end_str}\n"
                f"📋 {block_data['activity_type'].title()}"
            )

            if block_data.get('description'):
                summary += f"\n💬 {block_data['description']}"

            keyboard = build_add_more_blocks_keyboard()

            await update.message.reply_text(
                summary,
                parse_mode='Markdown',
                reply_markup=keyboard
            )

            return ADD_MORE

        else:
            await update.message.reply_text(
                "❌ Sorry, there was an error saving your schedule block. Please try again."
            )
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error saving schedule block: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )
        return ConversationHandler.END


async def handle_add_more(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle response to "add more blocks" question.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state or END
    """
    query = update.callback_query
    await query.answer()

    if query.data == "add_more_yes":
        # Clear previous block data
        context.user_data['schedule_block'] = {}

        keyboard = build_day_selection_keyboard()

        await query.edit_message_text(
            "Great! Let's add another time block.\n\n"
            "Which day?",
            reply_markup=keyboard
        )

        return DAY_SELECTION

    else:
        # Done adding blocks
        user = update.effective_user

        schedule_repo = ScheduleRepository()
        block_count = await schedule_repo.get_schedule_count(user.id)

        await query.edit_message_text(
            f"✅ *Schedule setup complete!*\n\n"
            f"You have {block_count} schedule block(s) set.\n\n"
            "What's next?\n"
            "• View your schedule: /viewschedule\n"
            "• Add goals: /newgoal\n"
            "• Generate your plan: /plan",
            parse_mode='Markdown'
        )

        # Clean up conversation data
        context.user_data.pop('schedule_block', None)

        return ConversationHandler.END


async def cancel_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel schedule setup.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        End of conversation
    """
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Schedule setup cancelled. Use /schedule when you're ready."
        )
    else:
        await update.message.reply_text(
            "Schedule setup cancelled. Use /schedule when you're ready."
        )

    # Clean up conversation data
    context.user_data.pop('schedule_block', None)

    return ConversationHandler.END


# Build the conversation handler
def get_schedule_conversation_handler() -> ConversationHandler:
    """
    Build and return the schedule conversation handler.

    Returns:
        ConversationHandler for schedule setup
    """
    return ConversationHandler(
        entry_points=[CommandHandler('schedule', start_schedule_conversation)],
        states={
            DAY_SELECTION: [
                CallbackQueryHandler(receive_day, pattern=r'^day_\d$')
            ],
            START_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_start_time)
            ],
            END_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_end_time)
            ],
            ACTIVITY_TYPE: [
                CallbackQueryHandler(receive_activity_type, pattern=r'^activity_')
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)
            ],
            ADD_MORE: [
                CallbackQueryHandler(handle_add_more, pattern=r'^add_more_(yes|no)$')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_schedule)
        ],
        conversation_timeout=900  # 15 minutes
    )
