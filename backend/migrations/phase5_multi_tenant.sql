-- Phase 5: Multi-Tenant SaaS Foundation
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- SKILL PROFILES TABLE - Track candidate skill history
-- =============================================================================
CREATE TABLE IF NOT EXISTS skill_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    score_history FLOAT[],
    latest_score FLOAT,
    consistency_score FLOAT,
    interview_count INTEGER DEFAULT 1,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, skill_name)
);

-- =============================================================================
-- INTERVIEW SESSION METRICS TABLE - For integrity monitoring
-- =============================================================================
CREATE TABLE IF NOT EXISTS interview_session_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    question_id UUID REFERENCES interview_questions(id) ON DELETE SET NULL,
    response_time_seconds FLOAT,
    pause_count INTEGER DEFAULT 0,
    total_pause_duration FLOAT DEFAULT 0,
    word_count INTEGER,
    speech_rate_words_per_minute FLOAT,
    audio_duration_seconds FLOAT,
    integrity_score FLOAT,
    flags JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- AI CACHE TABLE - Cache AI responses to reduce costs
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_hash TEXT NOT NULL UNIQUE,
    prompt_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    model_used TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);

-- =============================================================================
-- COMPANY DATA ISOLATION - Add company_id to existing tables
-- =============================================================================
-- Note: These columns already exist or are linked through jobs/companies

-- Add company_id to jobs if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'company_id'
    ) THEN
        ALTER TABLE jobs ADD COLUMN company_id UUID REFERENCES companies(id) ON DELETE CASCADE;
    END IF;
END
$$;

-- Add company_id to interviews if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'interviews' AND column_name = 'company_id'
    ) THEN
        ALTER TABLE interviews ADD COLUMN company_id UUID REFERENCES companies(id) ON DELETE SET NULL;
    END IF;
END
$$;

-- =============================================================================
-- ANALYTICS TABLES - Hiring intelligence
-- =============================================================================
CREATE TABLE IF NOT EXISTS job_skill_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    average_score FLOAT,
    total_candidates INTEGER DEFAULT 0,
    score_distribution JSONB DEFAULT '{}',
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, skill_name)
);

CREATE TABLE IF NOT EXISTS company_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_interviews INTEGER DEFAULT 0,
    total_candidates INTEGER DEFAULT 0,
    average_score FLOAT,
    jobs_created INTEGER DEFAULT 0,
    candidates_shortlisted INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, period_start, period_end)
);

-- =============================================================================
-- VECTOR EMBEDDINGS - Store as JSONB (cosine similarity computed in Python)
-- =============================================================================
CREATE TABLE IF NOT EXISTS skill_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_name TEXT NOT NULL UNIQUE,
    embedding JSONB NOT NULL,
    category TEXT,
    related_skills TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================
-- Skill profiles
CREATE INDEX IF NOT EXISTS idx_skill_profiles_user ON skill_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_profiles_skill ON skill_profiles(skill_name);

-- Interview session metrics
CREATE INDEX IF NOT EXISTS idx_session_metrics_interview ON interview_session_metrics(interview_id);
CREATE INDEX IF NOT EXISTS idx_session_metrics_integrity ON interview_session_metrics(integrity_score);

-- AI Cache
CREATE INDEX IF NOT EXISTS idx_ai_cache_hash ON ai_cache(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_ai_cache_expires ON ai_cache(expires_at);

-- Job skill analytics
CREATE INDEX IF NOT EXISTS idx_job_skill_analytics_job ON job_skill_analytics(job_id);

-- Skill embeddings
CREATE INDEX IF NOT EXISTS idx_skill_embeddings_name ON skill_embeddings(skill_name);

-- =============================================================================
-- ROW LEVEL SECURITY POLICIES
-- =============================================================================
ALTER TABLE skill_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_session_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_skill_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_embeddings ENABLE ROW LEVEL SECURITY;

-- Skill profiles: Users can read own, companies can read candidates
CREATE POLICY "Users can view own skill profile" ON skill_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Companies can view candidate skills" ON skill_profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM interviews i
            JOIN jobs j ON i.job_id = j.id
            WHERE i.candidate_id = skill_profiles.user_id
            AND j.company_id IN (
                SELECT company_id FROM profiles WHERE user_id = auth.uid()
            )
        )
    );

-- Interview session metrics: Recruiters can view their company's interviews
CREATE POLICY "Recruiters can view session metrics" ON interview_session_metrics
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM interviews i
            JOIN jobs j ON i.job_id = j.id
            WHERE i.id = interview_session_metrics.interview_id
            AND j.company_id IN (
                SELECT company_id FROM profiles WHERE user_id = auth.uid()
            )
        )
    );

-- AI cache: Read-only for authenticated users
CREATE POLICY "Auth users can read cache" ON ai_cache FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service can manage cache" ON ai_cache FOR ALL TO service_role USING (true);

-- Job skill analytics: Recruiters can view their jobs
CREATE POLICY "Recruiters can view job analytics" ON job_skill_analytics
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM jobs j
            WHERE j.id = job_skill_analytics.job_id
            AND j.company_id IN (
                SELECT company_id FROM profiles WHERE user_id = auth.uid()
            )
        )
    );

-- Company analytics: Company owners can view their analytics
CREATE POLICY "Company owners can view analytics" ON company_analytics
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM companies WHERE owner_id = auth.uid()
        )
    );

-- Skill embeddings: Public read
CREATE POLICY "Anyone can read skill embeddings" ON skill_embeddings FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service can manage embeddings" ON skill_embeddings FOR ALL TO service_role USING (true);

-- =============================================================================
-- VERIFICATION
-- =============================================================================
SELECT 'Tables created successfully' as status;
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'skill_profiles', 'interview_session_metrics', 'ai_cache',
    'job_skill_analytics', 'company_analytics', 'skill_embeddings'
);
