-- Telegram Goal Planning Bot - Database Schema
-- Execute this SQL in your Supabase SQL editor

-- ============================================
-- Table: users
-- Stores Telegram user information
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,  -- Telegram user ID
    username VARCHAR(255),
    first_name VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================
-- Table: goals
-- Stores user goals with AI clarification history
-- ============================================
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100),  -- e.g., 'fitness', 'education', 'career'
    target_date DATE,  -- When user wants to achieve this
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
    ai_clarifications JSONB DEFAULT '[]'::jsonb,  -- Store AI Q&A history
    metadata JSONB DEFAULT '{}'::jsonb,  -- Flexible field for additional goal details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_target_date ON goals(target_date);

-- ============================================
-- Table: weekly_schedules
-- Stores recurring weekly blocked times
-- ============================================
CREATE TABLE IF NOT EXISTS weekly_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),  -- 0=Monday, 6=Sunday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    activity_type VARCHAR(100) NOT NULL,  -- 'school', 'sport', 'work', 'personal'
    description TEXT,
    is_recurring BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

CREATE INDEX IF NOT EXISTS idx_weekly_schedules_user_id ON weekly_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_schedules_day ON weekly_schedules(day_of_week);

-- ============================================
-- Table: daily_tasks
-- AI-generated tasks with scheduled times
-- ============================================
CREATE TABLE IF NOT EXISTS daily_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    goal_id UUID REFERENCES goals(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,  -- Optimal time calculated by AI
    duration_minutes INTEGER DEFAULT 30,  -- Estimated task duration
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'skipped', 'rescheduled')),
    completed_at TIMESTAMP WITH TIME ZONE,
    ai_reasoning TEXT,  -- Why AI scheduled this task at this time
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_tasks_user_id ON daily_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_date ON daily_tasks(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_goal_id ON daily_tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_status ON daily_tasks(status);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_user_date ON daily_tasks(user_id, scheduled_date);

-- ============================================
-- Table: special_events
-- One-time events that may block scheduling
-- ============================================
CREATE TABLE IF NOT EXISTS special_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    is_all_day BOOLEAN DEFAULT FALSE,
    blocks_scheduling BOOLEAN DEFAULT TRUE,  -- Should tasks be scheduled around this?
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_event_time_range CHECK (end_time IS NULL OR start_time IS NULL OR end_time > start_time)
);

CREATE INDEX IF NOT EXISTS idx_special_events_user_id ON special_events(user_id);
CREATE INDEX IF NOT EXISTS idx_special_events_date ON special_events(event_date);

-- ============================================
-- Table: reminders
-- Scheduled reminder notifications
-- ============================================
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    task_id UUID REFERENCES daily_tasks(id) ON DELETE CASCADE,
    reminder_time TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(reminder_time);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_pending ON reminders(status, reminder_time) WHERE status = 'pending';

-- ============================================
-- Table: conversation_state
-- Stores multi-turn conversation context
-- ============================================
CREATE TABLE IF NOT EXISTS conversation_state (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    current_step VARCHAR(100),  -- Current conversation step
    context JSONB DEFAULT '{}'::jsonb,  -- Store conversation context
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Functions: Update timestamps automatically
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_goals_updated_at BEFORE UPDATE ON goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_tasks_updated_at BEFORE UPDATE ON daily_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_special_events_updated_at BEFORE UPDATE ON special_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversation_state_updated_at BEFORE UPDATE ON conversation_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Row Level Security (RLS) Policies (Optional)
-- Uncomment if you want to enable RLS
-- ============================================
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE weekly_schedules ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE daily_tasks ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE special_events ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_state ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (users can only see their own data):
-- CREATE POLICY "Users can view own data" ON goals
--     FOR SELECT USING (auth.uid()::bigint = user_id);
