# CogniVex AI Interview Platform - System Architecture & Design

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Database Schema](#database-schema)
5. [Backend API](#backend-api)
6. [Frontend Application](#frontend-application)
7. [AI Engine](#ai-engine)
8. [Authentication & Security](#authentication--security)
9. [Development Guide](#development-guide)
10. [Deployment](#deployment)

---

## Overview

CogniVex is an AI-powered hiring platform that automates the **first round of technical interviews** using voice-based AI conversations, automated evaluation, and intelligent candidate ranking.

### Core Value Proposition
- Companies receive hundreds of applications per job role
- Recruiters cannot manually interview every candidate
- CogniVex conducts AI-powered first-round interviews
- Candidates answer questions verbally, AI evaluates responses
- Platform generates structured scores and rankings
- Recruiters review top candidates efficiently

### User Types
| User Type | Description |
|-----------|-------------|
| **Candidate** | Job seekers who upload resumes and take AI interviews |
| **Recruiter** | Hiring managers who create jobs and review candidates |
| **Admin** | Platform administrators (future scope) |

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MOBILE APPLICATION                             │
│                    (React Native + Expo SDK 55)                          │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Candidate │  │   Interview │  │   Recruiter │  │   Profile   │     │
│  │   Dashboard │  │   Session   │  │   Dashboard │  │   Settings  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    API Client Layer                              │    │
│  │  - Centralized API client with retry logic                      │    │
│  │  - Token management & automatic refresh                          │    │
│  │  - Network status monitoring                                      │    │
│  │  - Error boundaries & loading states                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            BACKEND API                                  │
│                         (FastAPI + Python)                               │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │    Auth     │  │   Resume    │  │  Interview  │  │  Analytics  │     │
│  │   Router    │  │   Router    │  │   Router    │  │   Router    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │    Jobs     │  │  Dashboard  │  │  Recruiter  │  │  Rankings   │     │
│  │   Router    │  │   Router    │  │   Router    │  │   Router    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Service Layer                                 │    │
│  │  - InterviewSessionService  - EvaluationService                   │    │
│  │  - MatchingService          - ScoringService                      │    │
│  │  - ResumeService            - ReportService                       │    │
│  │  - GroqService (AI)         - SpeechService                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  Supabase   │ │    Groq     │ │   Deepgram  │
            │  PostgreSQL │ │  AI API     │ │  (Optional)  │
            │  + Storage  │ │  (LLaMA)    │ │  Speech API  │
            └─────────────┘ └─────────────┘ └─────────────┘
```

### Request Flow

```
Candidate Flow:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Register │ -> │  Upload  │ -> │   Get    │ -> │  Start   │ -> │  Answer  │
│ /Login   │    │ Resume   │    │Matches   │    │Interview │    │Questions │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                                     │
                                                                     ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  View    │ <- │   Get    │ <- │Generate  │ <- │Evaluate  │ <- │Transcribe│
│ Results  │    │  Report  │    │  Report   │    │ Answers  │    │  Audio   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘

Recruiter Flow:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Register │ -> │ Create   │ -> │  View    │ -> │Shortlist │
│ /Login   │    │ Company  │    │ Candidates│    │/ Reject  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                     │
                                     ▼
                              ┌──────────┐
                              │  View    │
                              │Analytics │
                              └──────────┘
```

---

## Technology Stack

### Backend (Python/FastAPI)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | FastAPI | Latest | Async REST API framework |
| **Database** | Supabase (PostgreSQL) | - | Primary data store with RLS |
| **Auth** | Supabase Auth | - | JWT-based authentication |
| **Storage** | Supabase Storage | - | File storage (resumes, audio) |
| **AI/LLM** | Groq API | - | LLaMA models for AI features |
| **Speech** | Deepgram (optional) | - | Speech-to-text transcription |
| **ORM** | Async Supabase Client | - | Async database operations |

### Frontend (React Native/Expo)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | React Native | 0.83.2 | Mobile cross-platform |
| **SDK** | Expo SDK | 55 | Development tooling |
| **Navigation** | Expo Router | ~55.0.7 | File-based routing |
| **Styling** | NativeWind | 4.2.2 | TailwindCSS for RN |
| **State** | React Context | - | Global state management |
| **Auth** | Supabase JS SDK | 2.99.1 | Client-side auth |
| **Audio** | expo-av | ~15.0.0 | Audio recording |
| **Network** | @react-native-community/netinfo | 11.5.2 | Network status |

### Infrastructure

| Component | Service | Purpose |
|-----------|---------|---------|
| **Database Hosting** | Supabase Cloud | PostgreSQL with auto-APIs |
| **File Storage** | Supabase Storage | Resume & audio files |
| **Auth Provider** | Supabase Auth | OAuth + Email/Password |
| **AI Provider** | Groq | Fast LLM inference |
| **CDN** | Supabase CDN | Static asset delivery |

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   profiles  │     │  companies  │     │    jobs     │
│─────────────│     │─────────────│     │─────────────│
│ id (UUID)   │     │ id (UUID)   │     │ id (UUID)   │
│ user_id ────┼────►│ owner_id    │     │ company_id  │
│ email       │     │ name        │     │ owner_id    │
│ full_name   │     │ description │     │ title       │
│ role        │     │ industry    │     │ description │
│ avatar_url  │     │ website     │     │ skills_req  │
│ created_at  │     │ location    │     │ experience  │
└─────────────┘     └─────────────┘     │ is_active   │
                    ▲                   └─────────────┘
                    │                          │
                    │                          │
┌─────────────┐     │                          │
│  resumes    │─────┤                          │
│─────────────│     │                          │
│ id (UUID)   │     │                          ▼
│ user_id     │     │                   ┌─────────────┐
│ file_url    │     │                   │ interviews  │
│ skills[]    │     │                   │─────────────│
│ exp_years   │     │                   │ id (UUID)   │
│ education[] │     │                   │ job_id      │
│ parsed_data │     │                   │ candidate_id│
└─────────────┘     │                   │ status      │
                    │                   │ difficulty  │
                    │                   │ max_questions│
                    │                   └─────────────┘
                    │                          │
                    │                          │
                    │                   ┌────┴────┐
                    │                   │         │
                    │              ┌────┴───┐ ┌───┴────┐
                    │              │questions│ │answers │
                    │              │────────│ │────────│
                    │              │id      │ │id      │
                    │              │interview_id│question_id│
                    │              │question_text│answer_text│
                    │              │skill    │ │score   │
                    │              │category │ │feedback│
                    │              └────────┘ └────────┘
                    │                          │
                    │                   ┌────┴────┐
                    │                   │         │
                    │              ┌────┴───┐ ┌───┴────┐
                    │              │ scores  │ │profiles │
                    │              │────────│ │────────│
                    │              │interview_id│user_id │
                    │              │overall_│ │full_name│
                    │              │technical│role    │
                    │              │commun. │ │created_at│
                    │              └────────┘ └────────┘
                    │
              ┌─────┴─────┐
              │ skill_    │
              │ embeddings│
              │───────────│
              │ skill     │
              │ embedding │
              └───────────┘
```

### Core Tables

#### `profiles`
Extends Supabase auth.users with application-specific data.

```sql
CREATE TABLE profiles (
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
```

#### `companies`
Recruiter-owned company records.

```sql
CREATE TABLE companies (
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
```

#### `jobs`
Job postings created by recruiters.

```sql
CREATE TABLE jobs (
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
```

#### `interviews`
Interview session management.

```sql
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    scheduled_at TIMESTAMPTZ,
    duration_minutes INTEGER DEFAULT 30,
    difficulty TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'scheduled',
    candidate_status TEXT DEFAULT 'pending',
    current_question_index INTEGER DEFAULT 0,
    max_questions INTEGER DEFAULT 7,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `interview_questions`
AI-generated questions for each interview.

```sql
CREATE TABLE interview_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_order INTEGER NOT NULL,
    skill TEXT,
    category TEXT,
    difficulty TEXT,
    time_limit_seconds INTEGER DEFAULT 120,
    expected_concepts TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `interview_answers`
Candidate responses with evaluation.

```sql
CREATE TABLE interview_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES interview_questions(id) ON DELETE CASCADE,
    answer_text TEXT,
    audio_url TEXT,
    transcript TEXT,
    score FLOAT,
    feedback TEXT,
    technical_accuracy FLOAT,
    communication_clarity FLOAT,
    concepts_detected TEXT[],
    concepts_missing TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `interview_scores`
Aggregated scores per interview.

```sql
CREATE TABLE interview_scores (
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
```

#### `resumes`
Uploaded resume data with AI-extracted skills.

```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT,
    skills TEXT[],
    experience_years INTEGER,
    education TEXT[],
    parsed_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Row Level Security (RLS) Policies

All tables have RLS enabled with policies ensuring:
- Users can only access their own profiles and resumes
- Candidates can only view their own interviews
- Recruiters can only manage their own companies and jobs
- Candidates can view active jobs but not modify them

---

## Backend API

### Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.cognivex.com/api/v1
```

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/signup` | Register new user | No |
| POST | `/auth/login` | Login with email/password | No |
| POST | `/auth/logout` | Logout current user | Yes |
| GET | `/auth/me` | Get current user | Yes |

**Request/Response Examples:**

```json
// POST /auth/signup
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}

// POST /auth/login
{
  "email": "user@example.com",
  "password": "securepassword123"
}

// Response
{
  "session": {
    "access_token": "eyJhbGc...",
    "refresh_token": "v2.local...",
    "expires_at": 1234567890
  },
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get current user profile |
| PUT | `/users/me` | Update profile |
| GET | `/users/{user_id}` | Get public profile |

### Company Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/companies` | Create company |
| GET | `/companies` | List user's companies |
| GET | `/companies/{id}` | Get company details |
| PUT | `/companies/{id}` | Update company |
| DELETE | `/companies/{id}` | Delete company |

### Job Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/jobs` | Create job posting |
| GET | `/jobs` | List jobs (with filters) |
| GET | `/jobs/{id}` | Get job details |
| PUT | `/jobs/{id}` | Update job |
| DELETE | `/jobs/{id}` | Delete job |
| GET | `/jobs/{id}/candidates` | Get matching candidates |
| GET | `/jobs/recommendations/for-me` | Get job recommendations (candidate) |
| GET | `/jobs/recommendations/candidate/{id}` | Get job recommendations (recruiter) |

### Interview Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/interviews` | Create interview session |
| GET | `/interviews` | List interviews |
| GET | `/interviews/{id}` | Get interview details |
| PUT | `/interviews/{id}` | Update interview |
| POST | `/interviews/{id}/start` | Start interview |
| POST | `/interviews/{id}/answer` | Submit text answer |
| POST | `/interviews/{id}/audio` | Submit audio answer |
| GET | `/interviews/{id}/next` | Get next question |
| GET | `/interviews/{id}/questions` | Get all questions |
| GET | `/interviews/{id}/score` | Get interview score |
| GET | `/interviews/{id}/report` | Get interview report |
| POST | `/interviews/{id}/complete` | Complete interview |
| GET | `/interviews/{id}/state` | Get session state |
| GET | `/interviews/{id}/transcript` | Get full transcript |
| POST | `/interviews/{id}/questions/progressive` | Generate progressive questions |
| POST | `/interviews/{id}/follow-up` | Generate follow-up question |
| POST | `/interviews/{id}/evaluate/detailed` | Detailed answer evaluation |
| POST | `/interviews/{id}/skills/aggregate` | Aggregate skill scores |
| POST | `/interviews/{id}/report/comprehensive` | Comprehensive report |

### Resume Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/resume/upload` | Upload and parse resume |
| GET | `/resume` | List user's resumes |
| GET | `/resume/{id}` | Get resume details |
| DELETE | `/resume/{id}` | Delete resume |
| PUT | `/resume/{id}/skills` | Update extracted skills |

### Dashboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/candidate` | Candidate dashboard data |
| GET | `/dashboard/candidate/profile` | Candidate profile |
| GET | `/dashboard/candidate/interviews` | Interview history |
| GET | `/dashboard/candidate/available` | Available interviews |
| GET | `/dashboard/candidate/results` | Past results |
| GET | `/dashboard/candidate/skills` | Skill profile |
| GET | `/dashboard/candidate/trend` | Performance trend |
| GET | `/dashboard/recruiter` | Recruiter dashboard |
| GET | `/dashboard/recruiter/company` | Company dashboard |
| GET | `/dashboard/recruiter/jobs` | Jobs with stats |
| GET | `/dashboard/recruiter/candidates-summary` | Candidates summary |
| GET | `/dashboard/stats` | User statistics |

### Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/jobs/{id}/skill-gaps` | Skill gap analysis |
| GET | `/analytics/jobs/{id}/trends` | Performance trends |
| GET | `/analytics/company/overview` | Company analytics |
| GET | `/analytics/company/top-candidates` | Top candidates |
| GET | `/analytics/users/{id}/skills` | User skill profile |
| GET | `/analytics/users/{id}/skills/top` | Top skills |
| GET | `/analytics/users/{id}/skills/improve` | Skills to improve |
| GET | `/analytics/skills/match` | Semantic skill matching |
| GET | `/analytics/interviews/{id}/integrity` | Interview integrity check |
| GET | `/analytics/cache/stats` | AI cache statistics |
| POST | `/analytics/cache/cleanup` | Cleanup expired cache |

### Recruiter Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/recruiter/dashboard` | Recruiter overview |
| GET | `/recruiter/jobs` | Jobs with candidate stats |
| GET | `/recruiter/jobs/{id}/candidates` | Job candidates |
| GET | `/recruiter/jobs/{id}/candidates/ranked` | Ranked candidates |
| POST | `/recruiter/candidates/{id}/status` | Update candidate status |
| GET | `/recruiter/jobs/{id}/shortlisted` | Shortlisted candidates |
| GET | `/recruiter/jobs/{id}/analytics` | Job analytics |
| GET | `/recruiter/candidates/{id}/report` | Detailed report |

### Ranking Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rankings/jobs/{id}/candidates` | All rankings |
| GET | `/rankings/jobs/{id}/candidates/ranked` | By interview score |
| GET | `/rankings/jobs/{id}/candidates/skill-match` | By skill match |
| GET | `/rankings/jobs/{id}/candidates/combined` | Combined ranking |
| GET | `/rankings/jobs/{id}/compare` | Compare candidates |
| GET | `/rankings/candidates/{id}/jobs` | Candidate rankings |
| POST | `/rankings/jobs/{id}/manage` | Manage job status |

---

## Frontend Application

### Project Structure

```
ai-interviewer/
├── app/                          # Expo Router screens
│   ├── (auth)/                    # Authentication flow
│   │   ├── _layout.tsx           # Auth stack navigator
│   │   └── onboarding.tsx        # Onboarding screen
│   ├── (tabs)/                    # Main tab navigation
│   │   ├── _layout.tsx           # Tab navigator
│   │   ├── index.tsx             # Home/Dashboard
│   │   ├── interviews.tsx         # Interviews list
│   │   ├── results.tsx           # Results screen
│   │   ├── recruiter.tsx         # Recruiter dashboard
│   │   └── profile.tsx            # User profile
│   ├── interview/                 # Interview flow
│   │   ├── _layout.tsx           # Interview navigator
│   │   ├── details.tsx           # Interview details
│   │   └── live.tsx              # Active interview
│   ├── _layout.tsx               # Root layout
│   └── upload-resume.tsx         # Resume upload screen
├── components/                    # Reusable components
│   ├── ErrorBoundary.tsx        # Error handling
│   ├── LoadingOverlay.tsx       # Loading states
│   └── NetworkStatus.tsx        # Network monitoring
├── contexts/                     # React contexts
│   └── AuthContext.tsx           # Authentication state
├── hooks/                        # Custom hooks
│   ├── useDashboard.ts           # Dashboard data
│   ├── useInterview.ts           # Interview logic
│   ├── useInterviews.ts          # Interviews list
│   ├── useRecruiter.ts           # Recruiter data
│   └── useNetworkStatus.ts       # Network status
├── lib/                          # Utilities & API
│   ├── api.ts                    # API types & config
│   ├── apiClient.ts              # Centralized API client
│   ├── audioRecorder.ts          # Audio recording
│   └── interviewApi.ts           # Interview API service
├── constants/                    # Constants
│   └── theme.ts                  # Theme & styling
├── types/                        # TypeScript types
│   └── index.ts                  # Type definitions
└── app.json                      # Expo configuration
```

### Navigation Flow

```
App Launch
    │
    ▼
Auth Check (AuthContext)
    │
    ├── Not Authenticated ──► Onboarding Screen
    │                               │
    │                               ▼
    │                          Login/Signup
    │                               │
    │                               ▼
    │                          Authenticated
    │                               │
    └──► Tab Navigator ◄─────────────┘
         │
         ├── Home Tab (index.tsx)
         │      ├── Job Recommendations
         │      ├── Resume Upload Prompt
         │      └── Active Interviews
         │
         ├── Interviews Tab
         │      ├── Interview List
         │      └── Interview Details
         │
         ├── Results Tab
         │      ├── Interview Results
         │      └── Score Reports
         │
         ├── Recruiter Tab (if recruiter)
         │      ├── Company Dashboard
         │      ├── Job Management
         │      └── Candidate Rankings
         │
         └── Profile Tab
                ├── User Info
                ├── Settings
                └── Logout
```

### Key Components

#### API Client (`lib/apiClient.ts`)
Centralized HTTP client with:
- Automatic token injection
- Token refresh on 401
- Retry logic with exponential backoff
- Request timeout handling
- Error normalization

```typescript
// Usage example
import { apiClient } from './apiClient';

const jobs = await apiClient.get<Job[]>('/jobs');
const interview = await apiClient.post<Interview>('/interviews', { job_id });
```

#### Auth Context (`contexts/AuthContext.tsx`)
Manages authentication state:
- Session persistence
- Token refresh
- User profile management

```typescript
// Usage example
const { user, signIn, signOut, getAccessToken } = useAuth();
```

#### Interview Hook (`hooks/useInterview.ts`)
Manages interview session:
- Question navigation
- Answer submission
- Score retrieval

```typescript
// Usage example
const {
  currentQuestion,
  submitAnswer,
  getScore,
  loading,
  error
} = useInterview(interviewId);
```

### Styling (NativeWind/TailwindCSS)

```typescript
// Theme constants (constants/theme.ts)
export const COLORS = {
  background: "#0B0B0C",
  backgroundLight: "#121212",
  card: "#1A1A1C",
  border: "#2A2A2C",
  surface: "#1E1E1E",
  primary: "#FFFFFF",
  text: "#FFFFFF",
  textMuted: "#8E8E93",
  success: "#10B981",
  error: "#EF4444",
  warning: "#F59E0B",
};

export const SPACING = {
  xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48
};
```

---

## AI Engine

### Groq Service (`backend/app/services/groq.py`)

The AI engine uses Groq's LLaMA models for:

#### 1. Resume Parsing
Extracts skills, experience, education from resume text.

```python
result = await groq_service.extract_resume_details(resume_text)
# Returns: { skills: [...], years_of_experience: int, education: "...", technologies: [...] }
```

#### 2. Question Generation
Creates interview questions based on job requirements.

```python
questions = await groq_service.generate_interview_questions_enhanced(
    job_title="Senior Backend Engineer",
    job_description="...",
    skills_required=["Python", "FastAPI", "PostgreSQL"],
    difficulty="medium",
    count=7
)
```

#### 3. Progressive Question Generation
Generates questions across difficulty levels.

```python
questions = await groq_service.generate_progressive_questions(
    skill="Python",
    job_title="Backend Engineer",
    candidate_level="intermediate",
    count_per_level=2
)
```

#### 4. Answer Evaluation
Multi-dimensional evaluation of candidate answers.

```python
evaluation = await groq_service.evaluate_answer_detailed(
    question={"question": "...", "skill": "Python", "expected_concepts": [...]},
    answer="Candidate's answer text",
    audio_transcript="Optional transcript"
)
# Returns: { quality, overall_score, dimensions, detected_concepts, feedback, ... }
```

#### 5. Follow-up Question Generation
Adaptive follow-ups based on answer quality.

```python
follow_up = await groq_service.generate_follow_up_question(
    original_question="...",
    candidate_answer="...",
    answer_evaluation={"quality": "good", "score": 85},
    skill="Python"
)
```

#### 6. Interview Report Generation
Comprehensive structured reports.

```python
report = await groq_service.generate_interview_report(
    candidate_name="John Doe",
    job_title="Senior Engineer",
    skill_evaluations=[...],
    skill_aggregates={...},
    interview_duration_minutes=30
)
```

### Matching Service (`backend/app/services/matching.py`)

Candidate-Job matching with skill scoring:

```python
# Skill match calculation
match = calculate_skill_match_score(
    candidate_skills=["Python", "FastAPI", "PostgreSQL"],
    required_skills=["Python", "Django", "Redis", "AWS"]
)
# Returns: { match_score: 25, matched_skills: ["Python"], missing_skills: ["Django", "Redis", "AWS"] }

# AI-powered matching
result = await matching_service.match_candidate_to_job(
    candidate_id="uuid",
    job_id="uuid"
)
```

### Evaluation Service (`backend/app/services/evaluation_service.py`)

Answer evaluation with concept detection:

```python
evaluation = await evaluation_service.evaluate_answer(
    question_id="uuid",
    transcript="Speech transcript",
    answer_text="Typed answer"
)
```

---

## Authentication & Security

### Supabase Auth Integration

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Mobile    │     │   Backend   │     │  Supabase   │
│    App      │     │    API      │     │    Auth     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                    │
       │  1. Login         │                    │
       │───────────────────────────────────────►│
       │                   │                    │
       │  2. JWT Token     │                    │
       │◄───────────────────────────────────────│
       │                   │                    │
       │  3. API Request   │                    │
       │  + Bearer Token   │                    │
       │──────────────────►│                    │
       │                   │                    │
       │                   │  4. Verify Token    │
       │                   │────────────────────►│
       │                   │                    │
       │                   │  5. User Data      │
       │                   │◄────────────────────│
       │                   │                    │
       │  6. Response      │                    │
       │◄──────────────────│                    │
```

### Token Management

```typescript
// Frontend: lib/apiClient.ts
private async getToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token || null;
}

private async refreshToken(): Promise<void> {
  const { error } = await supabase.auth.refreshSession();
  if (error) throw error;
}
```

### Backend Auth Middleware

```python
# backend/app/deps.py
async def get_current_user(
    authorization: Optional[str] = Header(None),
    supabase: AsyncClient = Depends(get_supabase)
) -> dict:
    if not authorization:
        raise UnauthorizedException("Authorization header missing")

    token = authorization.replace("Bearer ", "")
    user = await supabase.auth.get_user(token)

    if not user.user:
        raise UnauthorizedException("Invalid token")

    return user.user
```

### Row Level Security (RLS)

```sql
-- Profiles: Users can only access their own data
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = user_id);

-- Jobs: Only owners can modify
CREATE POLICY "Company owners can insert jobs" ON jobs
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

-- Interviews: Candidates and creators can access
CREATE POLICY "Users can view own interviews" ON interviews
    FOR SELECT USING (auth.uid() = candidate_id OR auth.uid() = created_by);
```

---

## Development Guide

### Prerequisites

- Node.js 18+
- Python 3.10+
- Supabase Account
- Groq API Key

### Environment Setup

#### Backend (.env)
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# AI
GROQ_API_KEY=your-groq-api-key

# Optional
DEEPGRAM_API_KEY=your-deepgram-key
```

#### Frontend (lib/api.ts)
```typescript
export const SUPABASE_URL = 'https://your-project.supabase.co';
export const SUPABASE_ANON_KEY = 'your-anon-key';
export const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### Running the Application

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
# Execute database.sql in Supabase SQL Editor

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
cd ai-interviewer

# Install dependencies
npm install

# Start Expo
npx expo start

# Run on Android
npx expo run:android

# Run on iOS
npx expo run:ios
```

### Database Setup

1. Create a Supabase project
2. Run `database.sql` in SQL Editor
3. Enable Row Level Security
4. Create Storage buckets:
   - `resumes` (public read)
   - `audio` (authenticated)

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

---

## Deployment

### Backend Deployment (Docker)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
    restart: unless-stopped
```

### Mobile App (Play Store)

#### Build APK
```bash
cd ai-interviewer

# Configure app.json
# Set package name, version, icons

# Build
npx expo prebuild --platform android
cd android
./gradlew assembleRelease
```

#### app.json Configuration
```json
{
  "expo": {
    "name": "CogniVex AI Interview",
    "slug": "cognivex-ai-interviewer",
    "version": "1.0.0",
    "android": {
      "package": "com.cognivex.interviewer",
      "permissions": [
        "RECORD_AUDIO",
        "INTERNET",
        "ACCESS_NETWORK_STATE"
      ]
    },
    "plugins": [
      "expo-router",
      ["expo-av", { "microphonePermission": "CogniVex needs microphone access..." }]
    ]
  }
}
```

---

## Key Architecture Decisions

### 1. Centralized API Client
**Decision**: Use a single `apiClient` instance for all HTTP requests.
**Rationale**:
- Consistent error handling
- Automatic token refresh
- Retry logic in one place
- Easier to add logging/monitoring

### 2. Progressive Interview Questions
**Decision**: Generate questions that increase in difficulty.
**Rationale**:
- Better assessment of candidate depth
- Adaptive to candidate responses
- More engaging interview experience

### 3. Multi-dimensional Scoring
**Decision**: Score answers across 5 dimensions.
**Rationale**:
- Technical accuracy alone is insufficient
- Communication skills matter for jobs
- Provides detailed feedback

### 4. Skill Embeddings for Matching
**Decision**: Use vector embeddings for semantic skill matching.
**Rationale**:
- "React" should match "React.js" and "React Native"
- Better candidate-job matching
- More accurate recommendations

### 5. Interview Integrity Monitoring
**Decision**: Track response patterns for cheating detection.
**Rationale**:
- Response time patterns
- Speech rate analysis
- Unusual pause detection
- Helps maintain interview authenticity

---

## Troubleshooting

### Common Issues

#### 1. "Cannot find module 'expo-router/internal/routing'"
**Cause**: SDK version mismatch between package.json and installed packages.
**Solution**:
```bash
rm -rf node_modules package-lock.json
npm install
```

#### 2. "Module not found: @supabase/supabase-js"
**Cause**: Missing dependency.
**Solution**:
```bash
npm install @supabase/supabase-js
```

#### 3. Authentication Errors (401)
**Cause**: Expired or invalid token.
**Solution**: Check token refresh logic in `apiClient.ts`.

#### 4. Database Connection Errors
**Cause**: Incorrect Supabase credentials or RLS policies.
**Solution**: Verify `.env` configuration and RLS policies.

---

## Future Enhancements

1. **Real-time Interview**: WebSocket support for live AI interviewer
2. **Video Interview**: Integration with video calling SDKs
3. **Multi-language Support**: Internationalization
4. **Advanced Analytics**: ML-based candidate insights
5. **Integration APIs**: Webhook support for ATS systems
6. **Offline Mode**: Local-first data strategy
7. **Push Notifications**: Interview reminders, status updates

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - See LICENSE file for details.