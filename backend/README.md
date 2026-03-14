# AI Interview Platform Backend

A FastAPI-based backend for an AI-powered interview platform with Supabase (PostgreSQL) and Groq AI integration.

## Features

- **Supabase Auth Integration** - JWT-based authentication
- **Resume Upload & Parsing** - Upload resumes and extract skills using AI
- **Job-Candidate Matching** - AI-powered matching between candidates and jobs
- **Interview Session Management** - Create and manage interview sessions
- **AI Answer Evaluation** - Real-time evaluation of candidate answers
- **Candidate Scoring** - Comprehensive scoring and feedback generation

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: Groq API
- **Authentication**: Supabase Auth (JWT)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Settings configuration
│   ├── deps.py                 # Dependencies (Supabase client)
│   ├── exceptions.py           # Custom exceptions
│   ├── models/                 # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py            # User, Profile, Company, Job models
│   │   ├── interview.py       # Interview, Question, Answer, Score models
│   │   └── response.py        # API response wrappers
│   ├── routers/                # API routes
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── users.py           # User profile endpoints
│   │   ├── companies.py       # Company management endpoints
│   │   ├── jobs.py            # Job posting endpoints
│   │   ├── interviews.py      # Interview session endpoints
│   │   └── resume.py          # Resume upload endpoints
│   └── services/              # Business logic
│       ├── __init__.py
│       ├── supabase.py        # Supabase client service
│       ├── groq.py            # Groq AI service
│       └── matching.py         # Candidate-job matching
├── .env.example
├── requirements.txt
├── database.sql               # Database schema
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `GROQ_API_KEY` - Your Groq API key

Optional:
- `DEEPGRAM_API_KEY` - For audio transcription
- `ELEVENTH_LABS_API_KEY` - For text-to-speech

### 3. Setup Database

Run the SQL in `database.sql` in your Supabase SQL Editor to create tables and configure RLS policies.

### 4. Run the Server

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users/me` - Get current user's profile
- `PUT /api/v1/users/me` - Update profile
- `GET /api/v1/users/{user_id}` - Get user profile

### Companies
- `POST /api/v1/companies` - Create company
- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/{id}` - Get company
- `PUT /api/v1/companies/{id}` - Update company
- `DELETE /api/v1/companies/{id}` - Delete company

### Jobs
- `POST /api/v1/jobs` - Create job posting
- `GET /api/v1/jobs` - List jobs
- `GET /api/v1/jobs/{id}` - Get job
- `PUT /api/v1/jobs/{id}` - Update job
- `DELETE /api/v1/jobs/{id}` - Delete job
- `GET /api/v1/jobs/{id}/candidates` - Get matching candidates

### Interviews
- `POST /api/v1/interviews` - Create interview
- `GET /api/v1/interviews` - List interviews
- `GET /api/v1/interviews/{id}` - Get interview
- `PUT /api/v1/interviews/{id}` - Update interview
- `POST /api/v1/interviews/{id}/answer` - Submit answer
- `GET /api/v1/interviews/{id}/score` - Get interview score

### Resume
- `POST /api/v1/resume/upload` - Upload resume
- `GET /api/v1/resume` - List resumes
- `GET /api/v1/resume/{id}` - Get resume
- `DELETE /api/v1/resume/{id}` - Delete resume
- `PUT /api/v1/resume/{id}/skills` - Update resume skills

## Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

## License

MIT
