"""
Plan and task management handlers.
Handles plan generation, task viewing, and task completion.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from datetime import date, timedelta
from services.planning_service import PlanningService
from database.repositories.task_repository import TaskRepository
from database.repositories.user_repository import UserRepository
from bot.keyboards import (
    build_task_list_keyboard,
    build_task_actions_keyboard,
    build_plan_view_selector,
    build_confirm_regenerate_keyboard
)
from utils.time_utils import get_week_dates, format_date_for_display
import logging

logger = logging.getLogger(__name__)


async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /plan command - generate AI-powered plan.

    Args:
        update: Telegram update
        context: Telegram context
    """
    user = update.effective_user

    # Send "generating" message
    generating_msg = await update.message.reply_text(
        "🤖 Generating your personalized plan...\n\n"
        "This may take a moment as I:\n"
        "• Analyze your goals\n"
        "• Review your schedule\n"
        "• Create optimized daily tasks\n\n"
        "Please wait..."
    )

    try:
        # Get user for timezone
        user_repo = UserRepository()
        user_data = await user_repo.get_user(user.id)
        timezone = user_data.get('timezone', 'UTC') if user_data else 'UTC'

        # Generate plan
        planning_service = PlanningService()
        result = await planning_service.generate_plan(
            user_id=user.id,
            plan_duration_days=30,
            timezone=timezone
        )

        # Delete generating message
        await generating_msg.delete()

        if result['success']:
            message = (
                "✅ *Plan Generated Successfully!*\n\n"
                f"📊 Created {result['task_count']} tasks\n"
                f"📅 Duration: {result['plan_duration_days']} days\n"
                f"🎯 Based on {result['goals_count']} goal(s)\n\n"
                "Your personalized plan is ready!\n\n"
                "View your tasks:\n"
                "• /today - See today's tasks\n"
                "• /week - See this week's tasks\n"
                "• /tasks - Browse all tasks"
            )

            keyboard = build_plan_view_selector()

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            error_messages = {
                "no_goals": (
                    "❌ You don't have any active goals yet!\n\n"
                    "Create your first goal with /newgoal\n"
                    "Then come back and use /plan to generate your action plan."
                ),
                "ai_failed": (
                    "❌ The AI couldn't generate a plan right now.\n\n"
                    "This might be a temporary issue. Please try again in a moment."
                ),
                "exception": f"❌ An error occurred:\n{result.get('message', 'Unknown error')}"
            }

            error_msg = error_messages.get(
                result.get('error'),
                "❌ Plan generation failed. Please try again."
            )

            await update.message.reply_text(error_msg)

    except Exception as e:
        logger.error(f"Error in plan_command: {e}")
        await generating_msg.delete()
        await update.message.reply_text(
            "❌ An unexpected error occurred. Please try again."
        )


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /today command - show today's tasks.

    Args:
        update: Telegram update
        context: Telegram context
    """
    user = update.effective_user

    try:
        task_repo = TaskRepository()
        today = date.today()

        tasks = await task_repo.get_tasks_for_date(user.id, today)

        if not tasks:
            await update.message.reply_text(
                "📅 *Today's Tasks*\n\n"
                "No tasks scheduled for today!\n\n"
                "Generate your plan with /plan",
                parse_mode='Markdown'
            )
            return

        # Count by status
        pending = [t for t in tasks if t['status'] == 'pending']
        completed = [t for t in tasks if t['status'] == 'completed']

        message = f"📅 *Today's Tasks* ({today.strftime('%A, %B %d')})\n\n"
        message += f"Total: {len(tasks)} | ✅ Done: {len(completed)} | 📝 Pending: {len(pending)}\n\n"

        # Show tasks
        for task in tasks:
            status_emoji = {
                'pending': '📝',
                'completed': '✅',
                'skipped': '⏭️',
                'rescheduled': '📅'
            }.get(task['status'], '📝')

            time_str = task['scheduled_time'][:5] if task.get('scheduled_time') else 'All day'

            message += f"{status_emoji} {time_str} - {task['title']}\n"

        message += "\nTap a task to view details:"

        keyboard = build_task_list_keyboard(tasks, show_date=False)

        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in today_command: {e}")
        await update.message.reply_text(
            "An error occurred while fetching today's tasks."
        )


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /week command - show this week's tasks.

    Args:
        update: Telegram update
        context: Telegram context
    """
    user = update.effective_user

    try:
        task_repo = TaskRepository()
        week_start, week_end = get_week_dates()

        tasks = await task_repo.get_tasks_by_date(user.id, week_start, week_end)

        if not tasks:
            await update.message.reply_text(
                "📆 *This Week's Tasks*\n\n"
                "No tasks scheduled for this week!\n\n"
                "Generate your plan with /plan",
                parse_mode='Markdown'
            )
            return

        # Count by status
        pending = [t for t in tasks if t['status'] == 'pending']
        completed = [t for t in tasks if t['status'] == 'completed']

        message = f"📆 *This Week's Tasks*\n"
        message += f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}\n\n"
        message += f"Total: {len(tasks)} | ✅ Done: {len(completed)} | 📝 Pending: {len(pending)}\n\n"
        message += "Tap a task to view details:"

        keyboard = build_task_list_keyboard(tasks, show_date=True)

        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in week_command: {e}")
        await update.message.reply_text(
            "An error occurred while fetching this week's tasks."
        )


async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for viewing a specific task's details.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        task_id = query.data.replace("view_task_", "")

        task_repo = TaskRepository()
        task = await task_repo.get_task(task_id)

        if not task:
            await query.edit_message_text("Task not found.")
            return

        # Format task details
        status_emoji = {
            'pending': '📝',
            'completed': '✅',
            'skipped': '⏭️',
            'rescheduled': '📅'
        }.get(task['status'], '📝')

        message = f"{status_emoji} *Task Details*\n\n"
        message += f"*Title:* {task['title']}\n"

        if task.get('description'):
            message += f"*Description:* {task['description']}\n"

        if task.get('scheduled_date'):
            date_obj = date.fromisoformat(task['scheduled_date'])
            message += f"*Date:* {format_date_for_display(date_obj)}\n"

        if task.get('scheduled_time'):
            message += f"*Time:* {task['scheduled_time'][:5]}\n"

        if task.get('duration_minutes'):
            message += f"*Duration:* {task['duration_minutes']} minutes\n"

        priority_stars = '⭐' * task.get('priority', 3)
        message += f"*Priority:* {priority_stars}\n"
        message += f"*Status:* {task['status'].title()}\n"

        if task.get('ai_reasoning'):
            message += f"\n*AI Note:* _{task['ai_reasoning']}_\n"

        if task.get('completed_at'):
            message += f"\n_Completed: {task['completed_at'][:16]}_"

        keyboard = build_task_actions_keyboard(task_id, task['status'])

        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error viewing task: {e}")
        await query.edit_message_text("An error occurred.")


async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for marking a task as complete.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        task_id = query.data.replace("complete_task_", "")

        task_repo = TaskRepository()
        updated_task = await task_repo.mark_task_complete(task_id)

        if updated_task:
            await query.edit_message_text(
                f"✅ *Task Completed!*\n\n"
                f"Great job on completing: *{updated_task['title']}*\n\n"
                "Keep up the momentum! 🎉\n\n"
                "View more tasks:\n"
                "• /today - Today's tasks\n"
                "• /week - This week",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("Failed to mark task as complete.")

    except Exception as e:
        logger.error(f"Error completing task: {e}")
        await query.edit_message_text("An error occurred.")


async def skip_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for skipping a task.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        task_id = query.data.replace("skip_task_", "")

        task_repo = TaskRepository()
        updated_task = await task_repo.mark_task_skipped(task_id)

        if updated_task:
            await query.edit_message_text(
                f"⏭️ *Task Skipped*\n\n"
                f"Skipped: *{updated_task['title']}*\n\n"
                "No worries! Focus on what matters most right now.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("Failed to skip task.")

    except Exception as e:
        logger.error(f"Error skipping task: {e}")
        await query.edit_message_text("An error occurred.")


async def delete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for deleting a task.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        task_id = query.data.replace("delete_task_", "")

        task_repo = TaskRepository()
        success = await task_repo.delete_task(task_id)

        if success:
            await query.edit_message_text(
                "🗑️ *Task Deleted*\n\n"
                "The task has been removed from your plan.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("Failed to delete task.")

    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        await query.edit_message_text("An error occurred.")


async def regenerate_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for regenerating the plan (show confirmation).

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    keyboard = build_confirm_regenerate_keyboard()

    await query.edit_message_text(
        "⚠️ *Regenerate Plan?*\n\n"
        "This will delete all pending tasks and create a fresh plan based on your current goals and schedule.\n\n"
        "Completed tasks will not be affected.\n\n"
        "Are you sure?",
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def confirm_regenerate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for confirming plan regeneration.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    await query.edit_message_text(
        "🤖 Regenerating your plan...\n\n"
        "Please wait..."
    )

    try:
        planning_service = PlanningService()
        result = await planning_service.regenerate_plan(user.id, plan_duration_days=30)

        if result['success']:
            message = (
                "✅ *Plan Regenerated!*\n\n"
                f"📊 Created {result['task_count']} new tasks\n"
                f"📅 Duration: {result['plan_duration_days']} days\n\n"
                "View your tasks:\n"
                "• /today\n"
                "• /week"
            )

            await query.edit_message_text(message, parse_mode='Markdown')
        else:
            await query.edit_message_text(
                "❌ Failed to regenerate plan. Please try /plan command."
            )

    except Exception as e:
        logger.error(f"Error regenerating plan: {e}")
        await query.edit_message_text("An error occurred.")


# Register all plan-related callback handlers
def get_plan_callback_handlers():
    """
    Get all callback handlers for plan management.

    Returns:
        List of CallbackQueryHandler instances
    """
    return [
        CallbackQueryHandler(view_task_callback, pattern=r'^view_task_'),
        CallbackQueryHandler(complete_task_callback, pattern=r'^complete_task_'),
        CallbackQueryHandler(skip_task_callback, pattern=r'^skip_task_'),
        CallbackQueryHandler(delete_task_callback, pattern=r'^delete_task_'),
        CallbackQueryHandler(regenerate_plan_callback, pattern=r'^regenerate_plan$'),
        CallbackQueryHandler(confirm_regenerate_callback, pattern=r'^confirm_regenerate$'),
    ]
