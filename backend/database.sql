-- Database Schema for AI Interview Platform
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    phone TEXT,
    location TEXT,
    headline TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    industry TEXT,
    website TEXT,
    logo_url TEXT,
    location TEXT,
    size TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    requirements TEXT[],
    skills_required TEXT[],
    location TEXT,
    job_type TEXT,
    experience_level TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Skills table
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT,
    skills TEXT[],
    experience_years INTEGER,
    education TEXT,
    parsed_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    scheduled_at TIMESTAMPTZ,
    duration_minutes INTEGER DEFAULT 30,
    difficulty TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'scheduled',
    candidate_status TEXT DEFAULT 'pending' CHECK (candidate_status IN ('pending', 'shortlisted', 'rejected', 'offered')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interview Questions table
CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_order INTEGER NOT NULL,
    time_limit_seconds INTEGER DEFAULT 120,
    category TEXT,
    difficulty TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interview Answers table
CREATE TABLE IF NOT EXISTS interview_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES interview_questions(id) ON DELETE CASCADE,
    answer_text TEXT,
    audio_url TEXT,
    transcript TEXT,
    score FLOAT,
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interview Scores table
CREATE TABLE IF NOT EXISTS interview_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID UNIQUE REFERENCES interviews(id) ON DELETE CASCADE,
    overall_score FLOAT,
    technical_score FLOAT,
    communication_score FLOAT,
    problem_solving_score FLOAT,
    cultural_fit_score FLOAT,
    strengths TEXT[],
    weaknesses TEXT[],
    summary TEXT,
    recommendation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security (RLS) Policies

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_scores ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Companies policies
CREATE POLICY "Anyone can view companies" ON companies FOR SELECT USING (true);
CREATE POLICY "Owners can insert companies" ON companies FOR INSERT WITH CHECK (auth.uid() = owner_id);
CREATE POLICY "Owners can update companies" ON companies FOR UPDATE USING (auth.uid() = owner_id);
CREATE POLICY "Owners can delete companies" ON companies FOR DELETE USING (auth.uid() = owner_id);

-- Jobs policies
CREATE POLICY "Anyone can view active jobs" ON jobs FOR SELECT USING (is_active = true);
CREATE POLICY "Company owners can insert jobs" ON jobs FOR INSERT WITH CHECK (auth.uid() = owner_id);
CREATE POLICY "Company owners can update jobs" ON jobs FOR UPDATE USING (auth.uid() = owner_id);
CREATE POLICY "Company owners can delete jobs" ON jobs FOR DELETE USING (auth.uid() = owner_id);

-- Skills policies
CREATE POLICY "Anyone can view skills" ON skills FOR SELECT USING (true);
CREATE POLICY "Anyone can insert skills" ON skills FOR INSERT WITH CHECK (true);

-- Resumes policies
CREATE POLICY "Users can view own resumes" ON resumes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own resumes" ON resumes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own resumes" ON resumes FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own resumes" ON resumes FOR DELETE USING (auth.uid() = user_id);

-- Interviews policies
CREATE POLICY "Users can view own interviews" ON interviews FOR SELECT USING (auth.uid() = candidate_id OR auth.uid() = created_by);
CREATE POLICY "Users can insert interviews" ON interviews FOR INSERT WITH CHECK (auth.uid() = created_by);
CREATE POLICY "Users can update own interviews" ON interviews FOR UPDATE USING (auth.uid() = candidate_id OR auth.uid() = created_by);

-- Interview Questions policies
CREATE POLICY "Anyone can view interview questions" ON interview_questions FOR SELECT USING (true);
CREATE POLICY "System can insert questions" ON interview_questions FOR INSERT WITH CHECK (true);
CREATE POLICY "System can update questions" ON interview_questions FOR UPDATE USING (true);

-- Interview Answers policies
CREATE POLICY "Users can manage own answers" ON interview_answers FOR ALL USING (
    EXISTS (
        SELECT 1 FROM interview_questions iq
        JOIN interviews i ON iq.interview_id = i.id
        WHERE iq.id = interview_answers.question_id
        AND i.candidate_id = auth.uid()
    )
);

-- Interview Scores policies
CREATE POLICY "Users can view own scores" ON interview_scores FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM interviews i
        WHERE i.id = interview_scores.interview_id
        AND (i.candidate_id = auth.uid() OR i.created_by = auth.uid())
    )
);

-- Storage buckets for file uploads (run separately if needed)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('resumes', 'resumes', true);

-- Storage policies
CREATE POLICY "Anyone can view resumes bucket" ON storage.objects FOR SELECT USING (bucket_id = 'resumes');
CREATE POLICY "Users can upload resumes" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'resumes' AND (storage.foldername(name))[1]::text = auth.uid()::text);
CREATE POLICY "Users can delete own resumes" ON storage.objects FOR DELETE USING (bucket_id = 'resumes' AND (storage.foldername(name))[1]::text = auth.uid()::text);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_company_id ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interviews_job_id ON interviews(job_id);
CREATE INDEX IF NOT EXISTS idx_interview_questions_interview_id ON interview_questions(interview_id);
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
