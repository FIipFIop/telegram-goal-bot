"""
AI service for OpenRouter API integration.
Handles goal clarification questions and plan generation.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)


class OpenRouterAI:
    """Service for interacting with OpenRouter API."""

    def __init__(self):
        """Initialize OpenRouter AI service."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        self.model = settings.OPENROUTER_MODEL

    async def generate_clarifying_questions(
        self,
        goal_title: str,
        goal_description: str,
        previous_qa: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate clarifying questions about a user's goal.

        Args:
            goal_title: The title of the goal
            goal_description: Initial description provided by user
            previous_qa: List of previous Q&A pairs (if any)

        Returns:
            Dict containing:
                - questions: List of clarifying questions
                - is_complete: Boolean indicating if enough info gathered
                - reasoning: Why these questions are being asked
        """
        try:
            # Build context from previous Q&A
            qa_context = ""
            if previous_qa:
                qa_context = "\n\nPrevious Q&A:\n"
                for qa in previous_qa:
                    qa_context += f"Q: {qa.get('question', '')}\nA: {qa.get('answer', '')}\n"

            # Create prompt for AI
            system_prompt = """You are a helpful goal-planning assistant. Your job is to ask clarifying questions to better understand user's goals.

Rules:
1. Ask 2-3 specific, relevant questions that will help create an actionable plan
2. Focus on: timeline, measurable outcomes, current situation, obstacles, resources, motivation
3. Don't ask questions if the information was already provided
4. After 3-5 rounds of questions, or when you have enough info, mark as complete
5. Be concise and friendly

Return your response in this exact JSON format:
{
    "questions": ["question 1", "question 2"],
    "is_complete": false,
    "reasoning": "Why these questions help"
}"""

            user_prompt = f"""Goal Title: {goal_title}
Goal Description: {goal_description}{qa_context}

Based on the goal and any previous answers, generate clarifying questions or mark as complete if you have enough information."""

            # Call OpenRouter API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            # Parse response
            content = response.choices[0].message.content.strip()

            # Try to extract JSON from the response
            try:
                # If the response is wrapped in markdown code blocks, extract it
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                result = json.loads(content)

                # Validate structure
                if "questions" not in result:
                    result["questions"] = []
                if "is_complete" not in result:
                    result["is_complete"] = False
                if "reasoning" not in result:
                    result["reasoning"] = "Gathering more information about your goal"

                logger.info(f"Generated {len(result['questions'])} questions for goal: {goal_title}")
                return result

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI response as JSON: {content}")
                # Fallback: treat the response as a single question
                return {
                    "questions": [content],
                    "is_complete": False,
                    "reasoning": "Need more details about your goal"
                }

        except Exception as e:
            logger.error(f"Error generating clarifying questions: {e}")
            return {
                "questions": [],
                "is_complete": True,
                "reasoning": "Error occurred, proceeding with available information"
            }

    async def analyze_goal_category(self, goal_title: str, goal_description: str) -> str:
        """
        Analyze and suggest a category for the goal.

        Args:
            goal_title: The title of the goal
            goal_description: Description of the goal

        Returns:
            Suggested category (e.g., 'fitness', 'education', 'career', etc.)
        """
        try:
            system_prompt = """Analyze the goal and return ONLY ONE WORD from this list:
fitness, health, education, career, finance, relationships, personal, creative, business, other

Return only the single most appropriate category word, nothing else."""

            user_prompt = f"Goal: {goal_title}\nDescription: {goal_description}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )

            category = response.choices[0].message.content.strip().lower()

            # Validate category
            valid_categories = [
                'fitness', 'health', 'education', 'career', 'finance',
                'relationships', 'personal', 'creative', 'business', 'other'
            ]

            if category in valid_categories:
                return category
            else:
                return 'other'

        except Exception as e:
            logger.error(f"Error analyzing goal category: {e}")
            return 'other'

    async def generate_plan(
        self,
        goals: List[Dict[str, Any]],
        weekly_schedule: List[Dict[str, Any]],
        special_events: List[Dict[str, Any]],
        timezone: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Generate an optimized plan with daily tasks for user's goals.

        Args:
            goals: List of user's goals with details
            weekly_schedule: User's weekly recurring blocked times
            special_events: One-time events that block scheduling
            timezone: User's timezone
            start_date: Plan start date (YYYY-MM-DD)
            end_date: Plan end date (YYYY-MM-DD)

        Returns:
            List of daily tasks with scheduling information
        """
        try:
            # Build context for AI
            goals_text = "\n".join([
                f"- {g['title']} (Priority: {g.get('priority', 3)}, Target: {g.get('target_date', 'Not set')})\n  {g.get('description', '')}"
                for g in goals
            ])

            schedule_text = "\n".join([
                f"- {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][s['day_of_week']]}: {s['start_time']}-{s['end_time']} ({s['activity_type']})"
                for s in weekly_schedule
            ]) if weekly_schedule else "No recurring schedule blocks"

            events_text = "\n".join([
                f"- {e['event_date']}: {e['title']}"
                for e in special_events
            ]) if special_events else "No special events"

            system_prompt = """You are an expert goal planning assistant. Create a structured daily task plan.

Rules:
1. Break down goals into small, actionable daily tasks
2. Distribute tasks evenly over the time period
3. Respect the user's schedule and avoid blocked times
4. Prioritize tasks by goal priority and deadline
5. Each task should take 15-60 minutes
6. Include reasoning for each task's timing

Return a JSON array of tasks with this structure:
[
    {
        "title": "Task title",
        "description": "What to do",
        "goal_title": "Related goal",
        "scheduled_date": "YYYY-MM-DD",
        "scheduled_time": "HH:MM",
        "duration_minutes": 30,
        "priority": 3,
        "reasoning": "Why scheduled at this time"
    }
]

Limit to maximum 50 tasks."""

            user_prompt = f"""Create a daily task plan:

Goals:
{goals_text}

Weekly Schedule (blocked times):
{schedule_text}

Special Events:
{events_text}

Period: {start_date} to {end_date}
Timezone: {timezone}

Generate an optimized task schedule."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                tasks = json.loads(content)

                if isinstance(tasks, list):
                    logger.info(f"Generated {len(tasks)} tasks for plan")
                    return tasks
                else:
                    logger.warning("AI response is not a list")
                    return []

            except json.JSONDecodeError:
                logger.error(f"Failed to parse plan as JSON: {content}")
                return []

        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return []
