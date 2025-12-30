"""
Goal management handlers for viewing, editing, and deleting goals.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.repositories.goal_repository import GoalRepository
from bot.keyboards import (
    build_goals_list_keyboard,
    build_goal_actions_keyboard,
    build_confirm_delete_keyboard
)
import logging

logger = logging.getLogger(__name__)


async def goals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /goals command - show list of user's goals.

    Args:
        update: Telegram update
        context: Telegram context
    """
    user = update.effective_user

    try:
        # Get user's goals
        goal_repo = GoalRepository()
        goals = await goal_repo.get_user_goals(user.id)

        if not goals:
            await update.message.reply_text(
                "You don't have any goals yet!\n\n"
                "Create your first goal with /newgoal"
            )
            return

        # Build goals list message
        active_goals = [g for g in goals if g['status'] == 'active']
        completed_goals = [g for g in goals if g['status'] == 'completed']

        message = f"*Your Goals*\n\n"
        message += f"📊 Total: {len(goals)} | Active: {len(active_goals)} | Completed: {len(completed_goals)}\n\n"
        message += "Select a goal to view details:"

        keyboard = build_goals_list_keyboard(goals)

        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in goals_command: {e}")
        await update.message.reply_text(
            "An error occurred while fetching your goals. Please try again."
        )


async def view_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for viewing a specific goal's details.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        # Extract goal ID from callback data
        goal_id = query.data.replace("view_goal_", "")

        # Get goal from database
        goal_repo = GoalRepository()
        goal = await goal_repo.get_goal(goal_id)

        if not goal:
            await query.edit_message_text(
                "Goal not found. It may have been deleted."
            )
            return

        # Format goal details
        status_emoji = {
            'active': '🎯',
            'completed': '✅',
            'paused': '⏸️',
            'cancelled': '❌'
        }.get(goal['status'], '🎯')

        message = f"{status_emoji} *{goal['title']}*\n\n"
        message += f"*Description:*\n{goal['description']}\n\n"

        if goal.get('category'):
            message += f"*Category:* {goal['category'].title()}\n"

        if goal.get('target_date'):
            message += f"*Target Date:* {goal['target_date']}\n"

        priority_stars = '⭐' * goal.get('priority', 3)
        message += f"*Priority:* {priority_stars}\n"
        message += f"*Status:* {goal['status'].title()}\n"

        # Show AI clarifications if any
        if goal.get('ai_clarifications') and len(goal['ai_clarifications']) > 0:
            message += f"\n*AI Clarifications:*\n"
            for qa in goal['ai_clarifications'][:3]:  # Show first 3
                message += f"• {qa.get('question', '')}\n  _{qa.get('answer', '')}_\n"

        message += f"\n_Created: {goal['created_at'][:10]}_"

        # Build action keyboard
        keyboard = build_goal_actions_keyboard(goal_id)

        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error viewing goal: {e}")
        await query.edit_message_text(
            "An error occurred while loading the goal details."
        )


async def complete_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for marking a goal as complete.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        goal_id = query.data.replace("complete_goal_", "")

        # Update goal status
        goal_repo = GoalRepository()
        updated_goal = await goal_repo.update_status(goal_id, 'completed')

        if updated_goal:
            await query.edit_message_text(
                f"✅ *Goal Completed!*\n\n"
                f"Congratulations on completing: *{updated_goal['title']}*\n\n"
                "Keep up the great work! 🎉\n\n"
                "View your goals: /goals\n"
                "Create a new goal: /newgoal",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "Failed to update goal status. Please try again."
            )

    except Exception as e:
        logger.error(f"Error completing goal: {e}")
        await query.edit_message_text(
            "An error occurred. Please try again."
        )


async def pause_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for pausing a goal.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        goal_id = query.data.replace("pause_goal_", "")

        goal_repo = GoalRepository()
        updated_goal = await goal_repo.update_status(goal_id, 'paused')

        if updated_goal:
            await query.edit_message_text(
                f"⏸️ *Goal Paused*\n\n"
                f"Goal: *{updated_goal['title']}*\n\n"
                "You can resume it anytime from /goals",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "Failed to pause goal. Please try again."
            )

    except Exception as e:
        logger.error(f"Error pausing goal: {e}")
        await query.edit_message_text(
            "An error occurred. Please try again."
        )


async def delete_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for initiating goal deletion (show confirmation).

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        goal_id = query.data.replace("delete_goal_", "")

        # Get goal to show title in confirmation
        goal_repo = GoalRepository()
        goal = await goal_repo.get_goal(goal_id)

        if not goal:
            await query.edit_message_text("Goal not found.")
            return

        keyboard = build_confirm_delete_keyboard(goal_id)

        await query.edit_message_text(
            f"⚠️ *Delete Goal?*\n\n"
            f"Are you sure you want to delete:\n*{goal['title']}*\n\n"
            f"This action cannot be undone!",
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in delete_goal_callback: {e}")
        await query.edit_message_text(
            "An error occurred. Please try again."
        )


async def confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for confirming goal deletion.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    try:
        goal_id = query.data.replace("confirm_delete_", "")

        # Delete goal
        goal_repo = GoalRepository()
        success = await goal_repo.delete_goal(goal_id)

        if success:
            await query.edit_message_text(
                "🗑️ *Goal Deleted*\n\n"
                "The goal has been permanently removed.\n\n"
                "View remaining goals: /goals\n"
                "Create a new goal: /newgoal",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "Failed to delete goal. Please try again."
            )

    except Exception as e:
        logger.error(f"Error confirming delete: {e}")
        await query.edit_message_text(
            "An error occurred. Please try again."
        )


async def back_to_goals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for going back to goals list.

    Args:
        update: Telegram update
        context: Telegram context
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    try:
        # Get user's goals
        goal_repo = GoalRepository()
        goals = await goal_repo.get_user_goals(user.id)

        if not goals:
            await query.edit_message_text(
                "You don't have any goals.\n\n"
                "Create your first goal with /newgoal"
            )
            return

        # Build goals list message
        active_goals = [g for g in goals if g['status'] == 'active']
        completed_goals = [g for g in goals if g['status'] == 'completed']

        message = f"*Your Goals*\n\n"
        message += f"📊 Total: {len(goals)} | Active: {len(active_goals)} | Completed: {len(completed_goals)}\n\n"
        message += "Select a goal to view details:"

        keyboard = build_goals_list_keyboard(goals)

        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in back_to_goals: {e}")
        await query.edit_message_text(
            "An error occurred. Please use /goals to view your goals."
        )


# Register all goal-related callback handlers
def get_goal_callback_handlers():
    """
    Get all callback handlers for goal management.

    Returns:
        List of CallbackQueryHandler instances
    """
    return [
        CallbackQueryHandler(view_goal_callback, pattern=r'^view_goal_'),
        CallbackQueryHandler(complete_goal_callback, pattern=r'^complete_goal_'),
        CallbackQueryHandler(pause_goal_callback, pattern=r'^pause_goal_'),
        CallbackQueryHandler(delete_goal_callback, pattern=r'^delete_goal_'),
        CallbackQueryHandler(confirm_delete_callback, pattern=r'^confirm_delete_'),
        CallbackQueryHandler(back_to_goals_callback, pattern=r'^back_to_goals$'),
    ]
