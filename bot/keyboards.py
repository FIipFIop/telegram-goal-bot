"""
Inline keyboard layouts for the Telegram bot.
Provides reusable keyboard builders for various bot interactions.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any


def build_priority_keyboard() -> InlineKeyboardMarkup:
    """
    Build keyboard for selecting goal priority.

    Returns:
        InlineKeyboardMarkup with priority options (1-5)
    """
    keyboard = [
        [
            InlineKeyboardButton("⭐ Low (1)", callback_data="priority_1"),
            InlineKeyboardButton("⭐⭐ (2)", callback_data="priority_2"),
        ],
        [
            InlineKeyboardButton("⭐⭐⭐ Medium (3)", callback_data="priority_3"),
        ],
        [
            InlineKeyboardButton("⭐⭐⭐⭐ (4)", callback_data="priority_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐ High (5)", callback_data="priority_5"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_yes_no_keyboard(yes_data: str = "yes", no_data: str = "no") -> InlineKeyboardMarkup:
    """
    Build a simple Yes/No keyboard.

    Args:
        yes_data: Callback data for Yes button
        no_data: Callback data for No button

    Returns:
        InlineKeyboardMarkup with Yes/No buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=yes_data),
            InlineKeyboardButton("❌ No", callback_data=no_data),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_goal_actions_keyboard(goal_id: str) -> InlineKeyboardMarkup:
    """
    Build keyboard for goal actions (view, edit, delete, complete).

    Args:
        goal_id: UUID of the goal

    Returns:
        InlineKeyboardMarkup with action buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_goal_{goal_id}"),
            InlineKeyboardButton("✅ Complete", callback_data=f"complete_goal_{goal_id}"),
        ],
        [
            InlineKeyboardButton("⏸️ Pause", callback_data=f"pause_goal_{goal_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_goal_{goal_id}"),
        ],
        [
            InlineKeyboardButton("« Back to Goals", callback_data="back_to_goals"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_goals_list_keyboard(goals: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Build keyboard displaying list of goals.

    Args:
        goals: List of goal dictionaries

    Returns:
        InlineKeyboardMarkup with goal buttons
    """
    keyboard = []

    for goal in goals[:10]:  # Limit to 10 goals to avoid message too long
        goal_id = goal['id']
        title = goal['title']
        status_emoji = {
            'active': '🎯',
            'completed': '✅',
            'paused': '⏸️',
            'cancelled': '❌'
        }.get(goal.get('status', 'active'), '🎯')

        # Truncate title if too long
        display_title = title[:40] + "..." if len(title) > 40 else title

        keyboard.append([
            InlineKeyboardButton(
                f"{status_emoji} {display_title}",
                callback_data=f"view_goal_{goal_id}"
            )
        ])

    # Add "Add New Goal" button at the bottom
    keyboard.append([
        InlineKeyboardButton("➕ Add New Goal", callback_data="new_goal")
    ])

    return InlineKeyboardMarkup(keyboard)


def build_category_keyboard() -> InlineKeyboardMarkup:
    """
    Build keyboard for selecting goal category.

    Returns:
        InlineKeyboardMarkup with category options
    """
    keyboard = [
        [
            InlineKeyboardButton("💪 Fitness", callback_data="category_fitness"),
            InlineKeyboardButton("❤️ Health", callback_data="category_health"),
        ],
        [
            InlineKeyboardButton("📚 Education", callback_data="category_education"),
            InlineKeyboardButton("💼 Career", callback_data="category_career"),
        ],
        [
            InlineKeyboardButton("💰 Finance", callback_data="category_finance"),
            InlineKeyboardButton("👥 Relationships", callback_data="category_relationships"),
        ],
        [
            InlineKeyboardButton("🎨 Creative", callback_data="category_creative"),
            InlineKeyboardButton("🏢 Business", callback_data="category_business"),
        ],
        [
            InlineKeyboardButton("✨ Personal", callback_data="category_personal"),
            InlineKeyboardButton("📋 Other", callback_data="category_other"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_confirm_delete_keyboard(goal_id: str) -> InlineKeyboardMarkup:
    """
    Build confirmation keyboard for goal deletion.

    Args:
        goal_id: UUID of the goal to delete

    Returns:
        InlineKeyboardMarkup with confirm/cancel buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("⚠️ Yes, Delete", callback_data=f"confirm_delete_{goal_id}"),
        ],
        [
            InlineKeyboardButton("« Cancel", callback_data=f"view_goal_{goal_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_skip_keyboard(skip_data: str = "skip") -> InlineKeyboardMarkup:
    """
    Build keyboard with a Skip button.

    Args:
        skip_data: Callback data for skip button

    Returns:
        InlineKeyboardMarkup with skip button
    """
    keyboard = [
        [
            InlineKeyboardButton("⏭️ Skip", callback_data=skip_data),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_continue_keyboard(continue_data: str = "continue") -> InlineKeyboardMarkup:
    """
    Build keyboard with Continue button.

    Args:
        continue_data: Callback data for continue button

    Returns:
        InlineKeyboardMarkup with continue button
    """
    keyboard = [
        [
            InlineKeyboardButton("Continue ➡️", callback_data=continue_data),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_day_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Build keyboard for selecting day of week.

    Returns:
        InlineKeyboardMarkup with day buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("Monday", callback_data="day_0"),
            InlineKeyboardButton("Tuesday", callback_data="day_1"),
        ],
        [
            InlineKeyboardButton("Wednesday", callback_data="day_2"),
            InlineKeyboardButton("Thursday", callback_data="day_3"),
        ],
        [
            InlineKeyboardButton("Friday", callback_data="day_4"),
            InlineKeyboardButton("Saturday", callback_data="day_5"),
        ],
        [
            InlineKeyboardButton("Sunday", callback_data="day_6"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_activity_type_keyboard() -> InlineKeyboardMarkup:
    """
    Build keyboard for selecting activity type.

    Returns:
        InlineKeyboardMarkup with activity type buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("🎓 School", callback_data="activity_school"),
            InlineKeyboardButton("⚽ Sport", callback_data="activity_sport"),
        ],
        [
            InlineKeyboardButton("💼 Work", callback_data="activity_work"),
            InlineKeyboardButton("👤 Personal", callback_data="activity_personal"),
        ],
        [
            InlineKeyboardButton("📋 Other", callback_data="activity_other"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_add_more_blocks_keyboard() -> InlineKeyboardMarkup:
    """
    Build keyboard asking if user wants to add more schedule blocks.

    Returns:
        InlineKeyboardMarkup with yes/no options
    """
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Another Block", callback_data="add_more_yes"),
        ],
        [
            InlineKeyboardButton("✅ Done", callback_data="add_more_no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_schedule_list_keyboard(schedules: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Build keyboard displaying list of schedule blocks.

    Args:
        schedules: List of schedule block dictionaries

    Returns:
        InlineKeyboardMarkup with schedule buttons
    """
    keyboard = []

    # Group schedules by day
    from collections import defaultdict
    by_day = defaultdict(list)
    for sched in schedules:
        by_day[sched['day_of_week']].append(sched)

    # Sort by day
    for day_num in sorted(by_day.keys()):
        day_schedules = by_day[day_num]
        for sched in day_schedules:
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_name = day_names[sched['day_of_week']]

            # Format: "Mon 9:00-17:00 (School)"
            label = f"{day_name} {sched['start_time'][:5]}-{sched['end_time'][:5]} ({sched['activity_type'].title()})"

            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"view_schedule_{sched['id']}")
            ])

    # Add "Add New Block" button at the bottom
    keyboard.append([
        InlineKeyboardButton("➕ Add New Block", callback_data="new_schedule_block")
    ])

    return InlineKeyboardMarkup(keyboard)


def build_schedule_block_actions_keyboard(schedule_id: str) -> InlineKeyboardMarkup:
    """
    Build keyboard for schedule block actions.

    Args:
        schedule_id: UUID of the schedule block

    Returns:
        InlineKeyboardMarkup with action buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("🗑️ Delete Block", callback_data=f"delete_schedule_{schedule_id}"),
        ],
        [
            InlineKeyboardButton("« Back to Schedule", callback_data="back_to_schedule"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_task_list_keyboard(tasks: List[Dict[str, Any]], show_date: bool = True) -> InlineKeyboardMarkup:
    """
    Build keyboard displaying list of tasks.

    Args:
        tasks: List of task dictionaries
        show_date: Whether to show dates in task labels

    Returns:
        InlineKeyboardMarkup with task buttons
    """
    keyboard = []

    for task in tasks[:15]:  # Limit to 15 tasks
        task_id = task['id']
        title = task['title']

        # Status emoji
        status_emoji = {
            'pending': '📝',
            'completed': '✅',
            'skipped': '⏭️',
            'rescheduled': '📅'
        }.get(task.get('status', 'pending'), '📝')

        # Build label
        if show_date and task.get('scheduled_date'):
            date_str = task['scheduled_date'][:5]  # MM-DD
            label = f"{status_emoji} {date_str}: {title[:30]}"
        else:
            label = f"{status_emoji} {title[:40]}"

        if len(title) > (30 if show_date else 40):
            label += "..."

        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"view_task_{task_id}")
        ])

    return InlineKeyboardMarkup(keyboard)


def build_task_actions_keyboard(task_id: str, task_status: str) -> InlineKeyboardMarkup:
    """
    Build keyboard for task actions.

    Args:
        task_id: UUID of the task
        task_status: Current task status

    Returns:
        InlineKeyboardMarkup with action buttons
    """
    keyboard = []

    if task_status == 'pending':
        keyboard.append([
            InlineKeyboardButton("✅ Mark Complete", callback_data=f"complete_task_{task_id}"),
        ])
        keyboard.append([
            InlineKeyboardButton("⏭️ Skip Task", callback_data=f"skip_task_{task_id}"),
            InlineKeyboardButton("📅 Reschedule", callback_data=f"reschedule_task_{task_id}"),
        ])

    keyboard.append([
        InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_task_{task_id}"),
    ])
    keyboard.append([
        InlineKeyboardButton("« Back", callback_data="back_to_tasks"),
    ])

    return InlineKeyboardMarkup(keyboard)


def build_plan_view_selector() -> InlineKeyboardMarkup:
    """
    Build keyboard for selecting plan view (today/week/month).

    Returns:
        InlineKeyboardMarkup with view selector buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("📅 Today", callback_data="view_today"),
            InlineKeyboardButton("📆 This Week", callback_data="view_week"),
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="view_stats"),
            InlineKeyboardButton("🔄 Regenerate Plan", callback_data="regenerate_plan"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_confirm_regenerate_keyboard() -> InlineKeyboardMarkup:
    """
    Build confirmation keyboard for plan regeneration.

    Returns:
        InlineKeyboardMarkup with confirm/cancel buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("⚠️ Yes, Regenerate", callback_data="confirm_regenerate"),
        ],
        [
            InlineKeyboardButton("« Cancel", callback_data="cancel_regenerate"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
