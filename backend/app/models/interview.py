from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InterviewDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# Interview schemas
class InterviewBase(BaseModel):
    job_id: str
    candidate_id: str
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 30
    difficulty: InterviewDifficulty = InterviewDifficulty.MEDIUM
    status: InterviewStatus = InterviewStatus.SCHEDULED


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    difficulty: Optional[InterviewDifficulty] = None
    status: Optional[InterviewStatus] = None


class InterviewResponse(InterviewBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    job: Optional[dict] = None
    candidate: Optional[dict] = None

    class Config:
        from_attributes = True


# Interview Question schemas
class InterviewQuestionBase(BaseModel):
    interview_id: str
    question_text: str
    question_order: int
    time_limit_seconds: Optional[int] = 120
    category: Optional[str] = None
    difficulty: Optional[InterviewDifficulty] = None


class InterviewQuestionCreate(InterviewQuestionBase):
    pass


class InterviewQuestionResponse(InterviewQuestionBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Interview Answer schemas
class InterviewAnswerBase(BaseModel):
    question_id: str
    answer_text: Optional[str] = None
    audio_url: Optional[str] = None
    transcript: Optional[str] = None


class InterviewAnswerCreate(InterviewAnswerBase):
    pass


class InterviewAnswerUpdate(BaseModel):
    answer_text: Optional[str] = None
    audio_url: Optional[str] = None
    transcript: Optional[str] = None


class InterviewAnswerResponse(InterviewAnswerBase):
    id: str
    score: Optional[float] = None
    feedback: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Interview Score schemas
class InterviewScoreBase(BaseModel):
    interview_id: str
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    communication_score: Optional[float] = None
    problem_solving_score: Optional[float] = None
    cultural_fit_score: Optional[float] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    summary: Optional[str] = None
    recommendation: Optional[str] = None  # hire, no_hire, uncertain


class InterviewScoreCreate(InterviewScoreBase):
    pass


class InterviewScoreUpdate(BaseModel):
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    communication_score: Optional[float] = None
    problem_solving_score: Optional[float] = None
    cultural_fit_score: Optional[float] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    summary: Optional[str] = None
    recommendation: Optional[str] = None


class InterviewScoreResponse(InterviewScoreBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Candidate Match schema
class CandidateMatch(BaseModel):
    candidate_id: str
    candidate_name: str
    candidate_email: str
    resume_id: Optional[str] = None
    skills_match_score: float
    experience_match_score: float
    overall_match_score: float
    matched_skills: List[str] = []
    missing_skills: List[str] = []
