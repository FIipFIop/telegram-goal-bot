# Telegram Goal Planning Bot

An AI-powered Telegram bot that helps you achieve your yearly goals by creating personalized plans, managing your schedule, and sending daily reminders.

## Features

- **Goal Setting**: Add yearly goals with AI-powered clarification questions
- **Smart Scheduling**: Respects your weekly schedule (school, sports, work, etc.)
- **AI-Powered Planning**: Uses OpenRouter API to create optimized daily action plans
- **Daily Reminders**: Automatic notifications to keep you on track
- **Special Events**: Manage one-time events that affect your schedule
- **Timezone Support**: Works with your local timezone
- **Progress Tracking**: Mark tasks as complete and track your progress

## Prerequisites

- Python 3.9 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Supabase Account (free tier available)
- OpenRouter API Key

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts to name your bot
4. Save the **Bot Token** you receive

### 2. Set Up Supabase Database

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Wait for the project to be provisioned
4. Go to **Project Settings** → **API**
5. Save your **Project URL** and **anon/public key**
6. Go to **SQL Editor**
7. Run the database schema from `migrations/init_schema.sql`

### 3. Get OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up for an account
3. Go to **Keys** section
4. Create a new API key
5. Save your API key

### 4. Install Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 5. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your credentials:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=xiaomi/mimo-v2-flash:free
LOG_LEVEL=INFO
```

### 6. Run the Bot

```bash
python main.py
```

You should see:
```
INFO - Starting Telegram Goal Planning Bot...
INFO - Bot initialized successfully
INFO - Bot is running. Press Ctrl+C to stop.
```

### 7. Test Your Bot

1. Open Telegram and search for your bot by username
2. Send `/start` command
3. Follow the bot's instructions!

## Usage Guide

### Getting Started

1. **Set Your Schedule** (`/schedule`)
   - Add your weekly recurring commitments (school, sports, work)
   - The bot will avoid scheduling tasks during these times

2. **Add Your Goals** (`/newgoal`)
   - Enter your goal title and description
   - Answer AI-generated clarifying questions
   - Set priority and target date

3. **Generate Your Plan** (`/plan`)
   - The AI analyzes your goals and schedule
   - Creates optimized daily tasks
   - Schedules reminders at appropriate times

4. **Stay on Track**
   - Receive daily reminders for your tasks
   - Mark tasks as complete with `/complete`
   - View today's tasks with `/today`

### Available Commands

#### Goal Management
- `/newgoal` - Add a new goal with AI assistance
- `/goals` - View and manage all your goals

#### Schedule Management
- `/schedule` - Set up weekly availability
- `/viewschedule` - See your current schedule
- `/newevent` - Add a special one-time event
- `/events` - View and manage your events

#### Planning & Tasks
- `/plan` - Generate AI-powered 30-day action plan
- `/today` - View today's tasks
- `/week` - View this week's tasks

#### Other
- `/start` - Initialize the bot
- `/help` - Show help message

## Project Structure

```
telegram achiving bot/
├── main.py                          # Entry point
├── config.py                        # Configuration management
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── .env                             # Environment variables (not in git)
├── README.md                        # This file
│
├── bot/
│   ├── handlers/                    # Command handlers
│   │   ├── start.py                 # /start and /help
│   │   ├── goals.py                 # Goal management
│   │   ├── schedule.py              # Schedule management
│   │   ├── events.py                # Event management
│   │   └── plan.py                  # Planning and tasks
│   │
│   ├── conversations/               # Multi-turn conversations
│   │   ├── goal_conversation.py     # Goal creation flow
│   │   ├── schedule_conversation.py # Schedule setup flow
│   │   └── event_conversation.py    # Event creation flow
│   │
│   └── keyboards.py                 # Inline keyboard builders
│
├── services/
│   ├── ai_service.py                # OpenRouter AI integration
│   ├── planning_service.py          # Task generation orchestration
│   ├── scheduler_service.py         # Background job scheduler
│   └── notification_service.py      # Telegram notifications
│
├── database/
│   ├── supabase_client.py           # Database client
│   └── repositories/                # Data access layer
│       ├── user_repository.py       # User operations
│       ├── goal_repository.py       # Goal CRUD
│       ├── schedule_repository.py   # Schedule blocks
│       ├── task_repository.py       # Daily tasks
│       ├── event_repository.py      # Special events
│       └── reminder_repository.py   # Reminder management
│
├── utils/
│   ├── validators.py                # Input validation
│   ├── time_utils.py                # Timezone utilities
│   ├── schedule_optimizer.py        # Available slot calculation
│   └── error_handler.py             # Error handling
│
└── migrations/
    └── init_schema.sql              # Database schema
```

## Development Status

### ✅ Phase 1: Foundation (COMPLETED)
- [x] Project structure
- [x] Database schema
- [x] Configuration management
- [x] Supabase client
- [x] User repository
- [x] Basic bot handlers (/start, /help)

### ✅ Phase 2: Goal Management (COMPLETED)
- [x] OpenRouter AI service
- [x] Goal repository
- [x] Goal conversation flow
- [x] AI clarification questions

### ✅ Phase 3: Schedule Management (COMPLETED)
- [x] Schedule repository
- [x] Schedule conversation flow
- [x] Time validation utilities
- [x] Schedule viewing/editing

### ✅ Phase 4: AI Planning (COMPLETED)
- [x] Planning service
- [x] Task repository
- [x] Schedule optimizer
- [x] Task viewing and completion

### ✅ Phase 5: Reminders (COMPLETED)
- [x] Scheduler service (APScheduler)
- [x] Reminder repository
- [x] Notification service
- [x] Timezone conversion utilities

### ✅ Phase 6: Special Events (COMPLETED)
- [x] Event repository
- [x] Event conversation handler
- [x] Event command handlers
- [x] Integration with planning

### ✅ Phase 7: Polish (COMPLETED)
- [x] Global error handling
- [x] Inline keyboards
- [x] Comprehensive logging
- [x] Conversation timeouts

## Troubleshooting

### Bot doesn't respond
- Check if `main.py` is running without errors
- Verify your `TELEGRAM_BOT_TOKEN` is correct
- Check logs for error messages

### Database errors
- Verify Supabase URL and key are correct
- Ensure you've run the schema SQL from `migrations/init_schema.sql`
- Check Supabase dashboard for connection issues

### AI not working (Phase 2+)
- Verify `OPENROUTER_API_KEY` is correct
- Check your OpenRouter account has credits
- Review logs for API errors

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions:
1. Check the logs in your terminal
2. Review the Supabase logs in your dashboard
3. Ensure all environment variables are set correctly

## Roadmap

Future enhancements:
- Voice input support
- Google Calendar integration
- Progress analytics and charts
- Habit tracking
- Collaboration features
- Mobile notifications
- Gamification (streaks, achievements)

---

Built with Python, python-telegram-bot, Supabase, and OpenRouter AI.
