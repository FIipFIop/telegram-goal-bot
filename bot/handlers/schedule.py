"""
Schedule viewing and management handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.repositories.schedule_repository import ScheduleRepository
from bot.keyboards import (
    build_schedule_list_keyboard,
    build_schedule_block_actions_keyboard
)
from utils.validators import get_day_name, format_time_24h
from datetime import time
import logging

logger = logging.getLogger(__name__)


async def viewschedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /viewschedule command - show user's weekly schedule.

    Args:
        update: Telegram update
        context: Telegram context
    """
    user = update.effective_user

    try:
        # Get user's schedule
        schedule_repo = ScheduleRepository()
        schedules = await schedule_repo.get_weekly_schedule(user.id)

        if not schedules:
            await update.message.reply_text(
                "You don't have any schedule blocks yet!\n\n"
                "Add your first schedule block with /schedule\n\n"
                "This helps me know when you're busy (school, sports, work, etc.) "
                "so I can schedule tasks at better times."
            )
            return

        # Build schedule visualization
        message = "*📅 Your Weekly Schedule*\n\n"

        # Group by day
        from collections import defaultdict
        by_day = defaultdict(list)
        for sched in schedules:
            by_day[sched['day_of_week']].append(sched)

        # Display schedule for each day
        for day_num in range(7):
            if day_num in by_day:
                day_name = get_day_name(day_num)
                message += f"*{day_name}:*\n"

                for block in by_day[day_num]:
                    start = block['start_time'][:5]  # HH:MM
                    end = block['end_time'][:5]
                    activity = block['activity_type'].title()

                    icon = {
                        'school': '🎓',
                        'sport': '⚽',
                        'work': '💼',
                        'personal': '👤',
                        'other': '📋'
                    }.get(block['activity_type'], '📋')

                    message += f"  {icon} {start}-{end} ({activity})\n"

                message += "\n"

        message += f"\nTotal blocks: {len(schedules)}\n\n"
        message += "Tap a block below to manage it:"

        # Build keyboard
        keyboard = build_schedule_list_keyboard(schedules)

        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in viewschedule_command: {e}")
        await update.message.reply_text(
            "An error occurred while fetching your schedule. Please try again."
        )


async def view_schedule_block_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for viewing a specific schedule block's details.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        # Extract schedule ID from callback data
        schedule_id = query.data.replace("view_schedule_", "")

        # Get schedule block from database
        schedule_repo = ScheduleRepository()
        block = await schedule_repo.get_schedule_block(schedule_id)

        if not block:
            await query.edit_message_text(
                "Schedule block not found. It may have been deleted."
            )
            return

        # Format block details
        day_name = get_day_name(block['day_of_week'])
        start_time = block['start_time'][:5]
        end_time = block['end_time'][:5]
        activity = block['activity_type'].title()

        icon = {
            'school': '🎓',
            'sport': '⚽',
            'work': '💼',
            'personal': '👤',
            'other': '📋'
        }.get(block['activity_type'], '📋')

        message = f"{icon} *Schedule Block*\n\n"
        message += f"*Day:* {day_name}\n"
        message += f"*Time:* {start_time} - {end_time}\n"
        message += f"*Activity:* {activity}\n"

        if block.get('description'):
            message += f"*Description:* {block['description']}\n"

        message += f"\n_Created: {block['created_at'][:10]}_"

        # Build action keyboard
        keyboard = build_schedule_block_actions_keyboard(schedule_id)

        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error viewing schedule block: {e}")
        await query.edit_message_text(
            "An error occurred while loading the schedule block details."
        )


async def delete_schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for deleting a schedule block.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        schedule_id = query.data.replace("delete_schedule_", "")

        # Delete schedule block
        schedule_repo = ScheduleRepository()
        success = await schedule_repo.delete_time_block(schedule_id)

        if success:
            await query.edit_message_text(
                "🗑️ *Schedule Block Deleted*\n\n"
                "The time block has been removed from your schedule.\n\n"
                "View your schedule: /viewschedule\n"
                "Add a new block: /schedule",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "Failed to delete schedule block. Please try again."
            )

    except Exception as e:
        logger.error(f"Error deleting schedule block: {e}")
        await query.edit_message_text(
            "An error occurred. Please try again."
        )


async def back_to_schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for going back to schedule list.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    try:
        # Get user's schedule
        schedule_repo = ScheduleRepository()
        schedules = await schedule_repo.get_weekly_schedule(user.id)

        if not schedules:
            await query.edit_message_text(
                "You don't have any schedule blocks.\n\n"
                "Add your first block with /schedule"
            )
            return

        # Build schedule visualization
        message = "*📅 Your Weekly Schedule*\n\n"

        # Group by day
        from collections import defaultdict
        by_day = defaultdict(list)
        for sched in schedules:
            by_day[sched['day_of_week']].append(sched)

        # Display schedule for each day
        for day_num in range(7):
            if day_num in by_day:
                day_name = get_day_name(day_num)
                message += f"*{day_name}:*\n"

                for block in by_day[day_num]:
                    start = block['start_time'][:5]
                    end = block['end_time'][:5]
                    activity = block['activity_type'].title()

                    icon = {
                        'school': '🎓',
                        'sport': '⚽',
                        'work': '💼',
                        'personal': '👤',
                        'other': '📋'
                    }.get(block['activity_type'], '📋')

                    message += f"  {icon} {start}-{end} ({activity})\n"

                message += "\n"

        message += f"\nTotal blocks: {len(schedules)}\n\n"
        message += "Tap a block to manage it:"

        # Build keyboard
        keyboard = build_schedule_list_keyboard(schedules)

        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in back_to_schedule: {e}")
        await query.edit_message_text(
            "An error occurred. Please use /viewschedule to view your schedule."
        )


async def new_schedule_block_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for adding a new schedule block from the view screen.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "To add a new schedule block, please use the /schedule command."
    )


# Register all schedule-related callback handlers
def get_schedule_callback_handlers():
    """
    Get all callback handlers for schedule management.

    Returns:
        List of CallbackQueryHandler instances
    """
    return [
        CallbackQueryHandler(view_schedule_block_callback, pattern=r'^view_schedule_'),
        CallbackQueryHandler(delete_schedule_callback, pattern=r'^delete_schedule_'),
        CallbackQueryHandler(back_to_schedule_callback, pattern=r'^back_to_schedule$'),
        CallbackQueryHandler(new_schedule_block_callback, pattern=r'^new_schedule_block$'),
    ]
