"""
Goal conversation handler for multi-turn goal creation with AI clarification.
Handles the complete flow from goal input to AI Q&A to final saving.
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
from datetime import datetime, timedelta
from database.repositories.goal_repository import GoalRepository
from services.ai_service import OpenRouterAI
from bot.keyboards import (
    build_priority_keyboard,
    build_category_keyboard,
    build_yes_no_keyboard,
    build_skip_keyboard
)
import logging

logger = logging.getLogger(__name__)

# Conversation states
TITLE, DESCRIPTION, AI_CLARIFICATION, CATEGORY, TARGET_DATE, PRIORITY, CONFIRM = range(7)


async def start_goal_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the goal creation conversation.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    # Initialize conversation data
    context.user_data['goal'] = {
        'qa_history': [],
        'ai_questions_asked': 0
    }

    await update.message.reply_text(
        "Let's create a new goal for you!\n\n"
        "First, what's the title of your goal?\n"
        "Example: 'Learn Spanish', 'Run a marathon', 'Save $10,000'\n\n"
        "Send /cancel anytime to stop."
    )

    return TITLE


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive and store goal title.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    title = update.message.text.strip()

    if len(title) < 3:
        await update.message.reply_text(
            "That's a bit too short. Please give your goal a more descriptive title:"
        )
        return TITLE

    if len(title) > 500:
        await update.message.reply_text(
            "That's too long! Please keep it under 500 characters:"
        )
        return TITLE

    # Store title
    context.user_data['goal']['title'] = title

    await update.message.reply_text(
        f"Great! Your goal: '{title}'\n\n"
        "Now, please describe your goal in more detail.\n"
        "What do you want to achieve? Why is this important to you?\n\n"
        "The more details you provide, the better I can help you plan!"
    )

    return DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive description and trigger AI clarification questions.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    description = update.message.text.strip()

    if len(description) < 10:
        await update.message.reply_text(
            "Please provide a bit more detail about your goal:"
        )
        return DESCRIPTION

    # Store description
    context.user_data['goal']['description'] = description

    # Send "thinking" message
    thinking_msg = await update.message.reply_text(
        "Thanks! Let me think about some questions to better understand your goal... 🤔"
    )

    try:
        # Get AI clarifying questions
        ai_service = OpenRouterAI()
        result = await ai_service.generate_clarifying_questions(
            goal_title=context.user_data['goal']['title'],
            goal_description=description,
            previous_qa=None
        )

        # Delete thinking message
        await thinking_msg.delete()

        if result.get('is_complete') or not result.get('questions'):
            # AI thinks we have enough info, skip to category
            await update.message.reply_text(
                "I have a good understanding of your goal! Let's continue with some details."
            )
            return await ask_category(update, context)

        # Store AI result
        context.user_data['goal']['current_questions'] = result['questions']
        context.user_data['goal']['ai_reasoning'] = result.get('reasoning', '')

        # Ask first question
        question_text = (
            f"I have a few questions to help create a better plan:\n\n"
            f"❓ {result['questions'][0]}"
        )

        await update.message.reply_text(question_text)

        # Track question index
        context.user_data['goal']['current_question_index'] = 0

        return AI_CLARIFICATION

    except Exception as e:
        logger.error(f"Error getting AI questions: {e}")
        await thinking_msg.delete()
        await update.message.reply_text(
            "I encountered an error. Let's continue without the clarification questions."
        )
        return await ask_category(update, context)


async def receive_ai_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive answer to AI clarification question.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    answer = update.message.text.strip()

    # Store Q&A
    current_index = context.user_data['goal']['current_question_index']
    current_questions = context.user_data['goal']['current_questions']

    qa_pair = {
        'question': current_questions[current_index],
        'answer': answer
    }
    context.user_data['goal']['qa_history'].append(qa_pair)

    # Check if more questions in current batch
    if current_index + 1 < len(current_questions):
        # Ask next question from current batch
        context.user_data['goal']['current_question_index'] += 1
        next_question = current_questions[current_index + 1]

        await update.message.reply_text(f"❓ {next_question}")
        return AI_CLARIFICATION

    # All questions from current batch answered
    # Check if we should ask more questions (max 5 rounds)
    context.user_data['goal']['ai_questions_asked'] += 1

    if context.user_data['goal']['ai_questions_asked'] >= 3:
        # Max questions reached, move to category
        await update.message.reply_text(
            "Thank you for the detailed information! 👍"
        )
        return await ask_category(update, context)

    # Get more AI questions
    thinking_msg = await update.message.reply_text("Let me think... 🤔")

    try:
        ai_service = OpenRouterAI()
        result = await ai_service.generate_clarifying_questions(
            goal_title=context.user_data['goal']['title'],
            goal_description=context.user_data['goal']['description'],
            previous_qa=context.user_data['goal']['qa_history']
        )

        await thinking_msg.delete()

        if result.get('is_complete') or not result.get('questions'):
            # AI has enough info
            await update.message.reply_text(
                "Perfect! I have all the information I need. 👍"
            )
            return await ask_category(update, context)

        # Ask new questions
        context.user_data['goal']['current_questions'] = result['questions']
        context.user_data['goal']['current_question_index'] = 0

        await update.message.reply_text(f"❓ {result['questions'][0]}")

        return AI_CLARIFICATION

    except Exception as e:
        logger.error(f"Error getting more AI questions: {e}")
        await thinking_msg.delete()
        return await ask_category(update, context)


async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Ask user to select goal category.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    keyboard = build_category_keyboard()

    message_text = (
        "What category does this goal belong to?\n"
        "This helps organize and plan your goals better."
    )

    if update.message:
        await update.message.reply_text(message_text, reply_markup=keyboard)
    else:
        await update.callback_query.message.reply_text(message_text, reply_markup=keyboard)

    return CATEGORY


async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive category selection.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    query = update.callback_query
    await query.answer()

    category = query.data.replace("category_", "")
    context.user_data['goal']['category'] = category

    await query.edit_message_text(
        f"Category: {category.title()} ✓\n\n"
        "When would you like to achieve this goal?\n"
        "Please send a date in format: YYYY-MM-DD\n"
        "Example: 2025-12-31\n\n"
        "Or send 'skip' if you don't have a specific date.",
        reply_markup=build_skip_keyboard("skip_target_date")
    )

    return TARGET_DATE


async def receive_target_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive target date for goal.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    if update.message:
        date_str = update.message.text.strip().lower()

        if date_str == 'skip':
            context.user_data['goal']['target_date'] = None
            await update.message.reply_text("Target date: Not set")
            return await ask_priority(update, context)

        # Try to parse date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Validate date is in the future
            if target_date <= datetime.now().date():
                await update.message.reply_text(
                    "Please choose a date in the future:"
                )
                return TARGET_DATE

            context.user_data['goal']['target_date'] = target_date
            await update.message.reply_text(f"Target date: {target_date} ✓")

            return await ask_priority(update, context)

        except ValueError:
            await update.message.reply_text(
                "Invalid date format. Please use YYYY-MM-DD\n"
                "Example: 2025-12-31\n\n"
                "Or send 'skip' to continue without a target date."
            )
            return TARGET_DATE

    else:
        # Callback from skip button
        query = update.callback_query
        await query.answer()
        context.user_data['goal']['target_date'] = None
        await query.edit_message_text("Target date: Not set")
        return await ask_priority(update, context)


async def ask_priority(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Ask for goal priority.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    keyboard = build_priority_keyboard()

    message_text = (
        "How important is this goal to you?\n"
        "Priority helps determine task scheduling."
    )

    if update.message:
        await update.message.reply_text(message_text, reply_markup=keyboard)
    else:
        await update.callback_query.message.reply_text(message_text, reply_markup=keyboard)

    return PRIORITY


async def receive_priority(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive priority selection and show confirmation.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        Next conversation state
    """
    query = update.callback_query
    await query.answer()

    priority = int(query.data.replace("priority_", ""))
    context.user_data['goal']['priority'] = priority

    # Build confirmation message
    goal_data = context.user_data['goal']
    confirmation_text = (
        "📝 *Goal Summary*\n\n"
        f"*Title:* {goal_data['title']}\n"
        f"*Description:* {goal_data['description']}\n"
        f"*Category:* {goal_data.get('category', 'Not set').title()}\n"
        f"*Target Date:* {goal_data.get('target_date', 'Not set')}\n"
        f"*Priority:* {'⭐' * priority}\n\n"
        "Save this goal?"
    )

    keyboard = build_yes_no_keyboard("save_goal", "cancel_goal")

    await query.edit_message_text(
        confirmation_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    return CONFIRM


async def save_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Save the goal to database.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        End of conversation
    """
    query = update.callback_query
    await query.answer()

    try:
        goal_data = context.user_data['goal']
        user = update.effective_user

        # Save to database
        goal_repo = GoalRepository()
        saved_goal = await goal_repo.create_goal(
            user_id=user.id,
            title=goal_data['title'],
            description=goal_data['description'],
            category=goal_data.get('category'),
            target_date=goal_data.get('target_date'),
            priority=goal_data.get('priority', 3),
            ai_clarifications=goal_data.get('qa_history', [])
        )

        if saved_goal:
            await query.edit_message_text(
                "✅ *Goal saved successfully!*\n\n"
                "What's next?\n"
                "• Add more goals with /newgoal\n"
                "• View your goals with /goals\n"
                "• Set your schedule with /schedule\n"
                "• Generate your plan with /plan",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Sorry, there was an error saving your goal. Please try again."
            )

    except Exception as e:
        logger.error(f"Error saving goal: {e}")
        await query.edit_message_text(
            "❌ An error occurred while saving your goal. Please try again later."
        )

    # Clean up conversation data
    context.user_data.pop('goal', None)

    return ConversationHandler.END


async def cancel_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel goal creation.

    Args:
        update: Telegram update
        context: Telegram context

    Returns:
        End of conversation
    """
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Goal creation cancelled. Use /newgoal when you're ready to create a goal."
        )
    else:
        await update.message.reply_text(
            "Goal creation cancelled. Use /newgoal when you're ready to create a goal."
        )

    # Clean up conversation data
    context.user_data.pop('goal', None)

    return ConversationHandler.END


# Build the conversation handler
def get_goal_conversation_handler() -> ConversationHandler:
    """
    Build and return the goal conversation handler.

    Returns:
        ConversationHandler for goal creation
    """
    return ConversationHandler(
        entry_points=[CommandHandler('newgoal', start_goal_conversation)],
        states={
            TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)
            ],
            AI_CLARIFICATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ai_answer)
            ],
            CATEGORY: [
                CallbackQueryHandler(receive_category, pattern=r'^category_')
            ],
            TARGET_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target_date),
                CallbackQueryHandler(receive_target_date, pattern=r'^skip_target_date$')
            ],
            PRIORITY: [
                CallbackQueryHandler(receive_priority, pattern=r'^priority_')
            ],
            CONFIRM: [
                CallbackQueryHandler(save_goal, pattern=r'^save_goal$'),
                CallbackQueryHandler(cancel_goal, pattern=r'^cancel_goal$')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_goal)
        ],
        conversation_timeout=900  # 15 minutes
    )
