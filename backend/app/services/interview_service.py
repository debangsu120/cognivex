"""Interview Session Service for managing interview state and flow."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from supabase import AsyncClient
from app.exceptions import AIException, SupabaseException
from app.services.groq import groq_service


class InterviewSessionState(str, Enum):
    """Interview session states."""
    CREATED = "created"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class QuestionCategory(str, Enum):
    """Interview question categories."""
    CONCEPT = "concept"
    APPLICATION = "application"
    ADVANCED = "advanced"


class QuestionDifficulty(str, Enum):
    """Interview question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# Constants
MAX_QUESTIONS = 7
MAX_DURATION_MINUTES = 15
DEFAULT_QUESTION_TIME_SECONDS = 120


class InterviewSessionService:
    """Service for managing interview session state and progression."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client for database operations
        """
        self.supabase = supabase_client
        self.max_questions = MAX_QUESTIONS
        self.max_duration = MAX_DURATION_MINUTES

    async def create_session(
        self,
        job_id: str,
        candidate_id: str,
        created_by: str,
        difficulty: str = "medium",
        max_questions: Optional[int] = None,
        duration_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new interview session.

        Args:
            job_id: Job ID for the interview
            candidate_id: Candidate user ID
            created_by: User ID creating the interview
            difficulty: Question difficulty level
            max_questions: Maximum questions (default 7)
            duration_minutes: Interview duration (default 15)

        Returns:
            Created interview session data
        """
        # Verify job exists
        job = await self.supabase.table("jobs").select("*").eq("id", job_id).execute()
        if not job.data:
            raise ValueError("Job not found")

        job_data = job.data[0]

        # Use provided values or defaults
        max_q = max_questions or MAX_QUESTIONS
        duration = duration_minutes or MAX_DURATION_MINUTES

        # Create interview record
        interview_data = {
            "job_id": job_id,
            "candidate_id": candidate_id,
            "created_by": created_by,
            "status": InterviewSessionState.READY.value,
            "difficulty": difficulty,
            "duration_minutes": duration,
            "max_questions": max_q,
            "current_question_index": 0,
            "started_at": None,
            "completed_at": None
        }

        response = await self.supabase.table("interviews").insert(interview_data).execute()

        if not response.data:
            raise SupabaseException("Failed to create interview session")

        interview = response.data[0]
        interview_id = interview["id"]

        # Generate questions using AI
        await self._generate_questions(
            interview_id=interview_id,
            job_title=job_data.get("title", ""),
            job_description=job_data.get("description", ""),
            skills_required=job_data.get("skills_required", []),
            difficulty=difficulty,
            count=max_q
        )

        # Fetch complete interview with questions
        complete_interview = await self.supabase.table("interviews").select(
            "*, jobs(*), interview_questions(*)"
        ).eq("id", interview_id).execute()

        return complete_interview.data[0]

    async def _generate_questions(
        self,
        interview_id: str,
        job_title: str,
        job_description: str,
        skills_required: List[str],
        difficulty: str,
        count: int
    ) -> None:
        """Generate interview questions using AI and save to database.

        Args:
            interview_id: Interview session ID
            job_title: Job title
            job_description: Job description
            skills_required: List of required skills
            difficulty: Difficulty level
            count: Number of questions to generate
        """
        try:
            questions = await groq_service.generate_interview_questions_enhanced(
                job_title=job_title,
                job_description=job_description,
                skills_required=skills_required,
                difficulty=difficulty,
                count=count
            )

            # Save questions to database
            for i, q in enumerate(questions):
                question_data = {
                    "interview_id": interview_id,
                    "question_text": q.get("question", ""),
                    "question_order": i + 1,
                    "skill": q.get("skill"),
                    "category": q.get("category", QuestionCategory.APPLICATION.value),
                    "difficulty": q.get("difficulty", difficulty),
                    "time_limit_seconds": DEFAULT_QUESTION_TIME_SECONDS
                }
                await self.supabase.table("interview_questions").insert(question_data).execute()

        except Exception as e:
            raise AIException(f"Failed to generate questions: {str(e)}")

    async def start_interview(self, interview_id: str) -> Dict[str, Any]:
        """Start an interview session.

        Args:
            interview_id: Interview ID to start

        Returns:
            Updated interview data
        """
        # Get current interview
        interview = await self.supabase.table("interviews").select("*").eq("id", interview_id).execute()
        if not interview.data:
            raise ValueError("Interview not found")

        interview_data = interview.data[0]

        # Check if already started or completed
        if interview_data.get("status") in [
            InterviewSessionState.IN_PROGRESS.value,
            InterviewSessionState.COMPLETED.value
        ]:
            raise ValueError("Interview already started or completed")

        # Update status to in_progress
        now = datetime.utcnow()
        update_data = {
            "status": InterviewSessionState.IN_PROGRESS.value,
            "started_at": now.isoformat(),
            "current_question_index": 1
        }

        response = await self.supabase.table("interviews").update(update_data).eq("id", interview_id).execute()

        if not response.data:
            raise SupabaseException("Failed to start interview")

        # Get complete interview with questions
        return await self.get_interview_with_questions(interview_id)

    async def get_questions(self, interview_id: str) -> List[Dict[str, Any]]:
        """Get all questions for an interview.

        Args:
            interview_id: Interview ID

        Returns:
            List of interview questions
        """
        response = await self.supabase.table("interview_questions").select(
            "*"
        ).eq("interview_id", interview_id).order("question_order").execute()

        return response.data

    async def get_current_question(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Get the current question for an interview.

        Args:
            interview_id: Interview ID

        Returns:
            Current question data or None
        """
        # Get interview state
        interview = await self.supabase.table("interviews").select(
            "current_question_index, status, started_at"
        ).eq("id", interview_id).execute()

        if not interview.data:
            raise ValueError("Interview not found")

        interview_data = interview.data[0]
        current_index = interview_data.get("current_question_index", 1)

        # Check for timeout
        if interview_data.get("started_at"):
            started_at = datetime.fromisoformat(interview_data["started_at"].replace("Z", "+00:00"))
            elapsed = datetime.utcnow() - started_at.replace(tzinfo=None)
            if elapsed > timedelta(minutes=self.max_duration):
                await self._mark_timeout(interview_id)
                raise ValueError("Interview time limit exceeded")

        # Get current question
        response = await self.supabase.table("interview_questions").select(
            "*"
        ).eq("interview_id", interview_id).eq("question_order", current_index).execute()

        if response.data:
            question = response.data[0]

            # Check if already answered
            answer = await self.supabase.table("interview_answers").select(
                "*"
            ).eq("question_id", question["id"]).execute()

            return {
                **question,
                "already_answered": len(answer.data) > 0,
                "answer": answer.data[0] if answer.data else None,
                "time_remaining": self._calculate_time_remaining(interview_data)
            }

        return None

    def _calculate_time_remaining(self, interview_data: Dict) -> Optional[int]:
        """Calculate remaining time for interview.

        Args:
            interview_data: Interview data with started_at

        Returns:
            Seconds remaining or None if not started
        """
        if not interview_data.get("started_at"):
            return None

        started_at = datetime.fromisoformat(interview_data["started_at"].replace("Z", "+00:00"))
        duration = interview_data.get("duration_minutes", MAX_DURATION_MINUTES)

        elapsed = datetime.utcnow() - started_at.replace(tzinfo=None)
        remaining = (duration * 60) - elapsed.total_seconds()

        return max(0, int(remaining))

    async def get_next_question(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Get the next question in the interview.

        Args:
            interview_id: Interview ID

        Returns:
            Next question data or None if no more questions
        """
        # Get interview state
        interview = await self.supabase.table("interviews").select(
            "current_question_index, max_questions"
        ).eq("id", interview_id).execute()

        if not interview.data:
            raise ValueError("Interview not found")

        interview_data = interview.data[0]
        current_index = interview_data.get("current_question_index", 0)
        max_questions = interview_data.get("max_questions", MAX_QUESTIONS)

        # Check if more questions available
        if current_index >= max_questions:
            return None

        # Move to next question
        next_index = current_index + 1

        await self.supabase.table("interviews").update({
            "current_question_index": next_index
        }).eq("id", interview_id).execute()

        # Get the next question
        response = await self.supabase.table("interview_questions").select(
            "*"
        ).eq("interview_id", interview_id).eq("question_order", next_index).execute()

        if response.data:
            return response.data[0]

        return None

    async def submit_answer(
        self,
        interview_id: str,
        question_id: str,
        answer_text: Optional[str] = None,
        audio_url: Optional[str] = None,
        transcript: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit an answer to a question.

        Args:
            interview_id: Interview ID
            question_id: Question ID
            answer_text: Text answer
            audio_url: Audio recording URL
            transcript: Speech-to-text transcript

        Returns:
            Answer data with evaluation
        """
        # Verify interview exists and is in progress
        interview = await self.supabase.table("interviews").select(
            "*, jobs(*)"
        ).eq("id", interview_id).execute()

        if not interview.data:
            raise ValueError("Interview not found")

        interview_data = interview.data[0]

        if interview_data.get("status") != InterviewSessionState.IN_PROGRESS.value:
            raise ValueError("Interview is not in progress")

        # Verify question belongs to this interview
        question = await self.supabase.table("interview_questions").select(
            "*"
        ).eq("id", question_id).eq("interview_id", interview_id).execute()

        if not question.data:
            raise ValueError("Question not found in this interview")

        question_data = question.data[0]

        # Get job skills for evaluation
        job_data = interview_data.get("jobs", {})
        skills_required = job_data.get("skills_required", [])

        # Evaluate answer using AI
        evaluation = await groq_service.evaluate_answer(
            question=question_data.get("question_text", ""),
            answer=answer_text or "",
            skills_required=skills_required
        )

        # Check if answer already exists
        existing = await self.supabase.table("interview_answers").select(
            "*"
        ).eq("question_id", question_id).execute()

        answer_data = {
            "question_id": question_id,
            "answer_text": answer_text,
            "audio_url": audio_url,
            "transcript": transcript,
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get("feedback", ""),
            "technical_accuracy": evaluation.get("technical_accuracy", 0),
            "communication_clarity": evaluation.get("communication_clarity", 0)
        }

        if existing.data:
            # Update existing answer
            response = await self.supabase.table("interview_answers").update(
                answer_data
            ).eq("id", existing.data[0]["id"]).execute()
        else:
            # Create new answer
            response = await self.supabase.table("interview_answers").insert(
                answer_data
            ).execute()

        # Check if all questions are answered
        await self._check_and_complete_interview(interview_id)

        return {
            **response.data[0],
            "evaluation": evaluation
        }

    async def _check_and_complete_interview(self, interview_id: str) -> None:
        """Check if interview is complete and generate final scores.

        Args:
            interview_id: Interview ID
        """
        # Get all questions
        questions = await self.supabase.table("interview_questions").select(
            "id"
        ).eq("interview_id", interview_id).execute()

        # Get all answers
        answers = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).execute()

        # Check if all questions answered or max reached
        interview = await self.supabase.table("interviews").select(
            "max_questions, status"
        ).eq("id", interview_id).execute()

        if not interview.data:
            return

        interview_data = interview.data[0]

        # If all questions answered or max reached, complete interview
        if len(answers.data) >= len(questions.data) or \
           len(answers.data) >= interview_data.get("max_questions", MAX_QUESTIONS):
            await self._complete_interview(interview_id, answers.data)

    async def _complete_interview(self, interview_id: str, answers: List[Dict]) -> None:
        """Complete interview and generate overall feedback.

        Args:
            interview_id: Interview ID
            answers: List of all answers
        """
        # Get interview with job
        interview = await self.supabase.table("interviews").select(
            "*, jobs(*)"
        ).eq("id", interview_id).execute()

        if not interview.data:
            return

        job_data = interview.data[0].get("jobs", {})

        # Generate overall feedback
        feedback = await groq_service.generate_overall_feedback(
            interview_answers=answers,
            job_title=job_data.get("title", "Position")
        )

        # Save or update score
        existing_score = await self.supabase.table("interview_scores").select(
            "*"
        ).eq("interview_id", interview_id).execute()

        score_data = {
            "interview_id": interview_id,
            "overall_score": feedback.get("overall_score", 0),
            "technical_score": feedback.get("technical_score", 0),
            "communication_score": feedback.get("communication_score", 0),
            "problem_solving_score": feedback.get("problem_solving_score", 0),
            "cultural_fit_score": feedback.get("cultural_fit_score", 0),
            "strengths": feedback.get("strengths", []),
            "weaknesses": feedback.get("weaknesses", []),
            "summary": feedback.get("summary", ""),
            "recommendation": feedback.get("recommendation", "uncertain")
        }

        if existing_score.data:
            await self.supabase.table("interview_scores").update(score_data).eq(
                "interview_id", interview_id
            ).execute()
        else:
            await self.supabase.table("interview_scores").insert(score_data).execute()

        # Update interview status
        await self.supabase.table("interviews").update({
            "status": InterviewSessionState.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", interview_id).execute()

    async def _mark_timeout(self, interview_id: str) -> None:
        """Mark interview as timed out.

        Args:
            interview_id: Interview ID
        """
        await self.supabase.table("interviews").update({
            "status": InterviewSessionState.TIMEOUT.value
        }).eq("id", interview_id).execute()

    async def get_interview_with_questions(self, interview_id: str) -> Dict[str, Any]:
        """Get complete interview with questions and answers.

        Args:
            interview_id: Interview ID

        Returns:
            Complete interview data
        """
        response = await self.supabase.table("interviews").select(
            "*, jobs(*), interview_questions(*), interview_answers(*), interview_scores(*)"
        ).eq("id", interview_id).execute()

        if not response.data:
            raise ValueError("Interview not found")

        return response.data[0]

    async def complete_interview(self, interview_id: str) -> Dict[str, Any]:
        """Manually complete an interview.

        Args:
            interview_id: Interview ID

        Returns:
            Completed interview data with scores
        """
        # Get all answers
        answers = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).execute()

        # Complete the interview
        await self._complete_interview(interview_id, answers.data)

        # Return final interview data
        return await self.get_interview_with_questions(interview_id)

    async def get_session_state(self, interview_id: str) -> Dict[str, Any]:
        """Get current session state.

        Args:
            interview_id: Interview ID

        Returns:
            Session state information
        """
        interview = await self.supabase.table("interviews").select(
            "*, jobs(*)"
        ).eq("id", interview_id).execute()

        if not interview.data:
            raise ValueError("Interview not found")

        data = interview.data[0]

        # Get question count
        questions = await self.supabase.table("interview_questions").select(
            "id"
        ).eq("interview_id", interview_id).execute()

        # Get answer count
        answers = await self.supabase.table("interview_answers").select(
            "id"
        ).eq("interview_questions.interview_id", interview_id).execute()

        return {
            "interview_id": interview_id,
            "status": data.get("status"),
            "current_question_index": data.get("current_question_index", 0),
            "total_questions": len(questions.data),
            "answered_questions": len(answers.data),
            "max_questions": data.get("max_questions", MAX_QUESTIONS),
            "duration_minutes": data.get("duration_minutes", MAX_DURATION_MINUTES),
            "started_at": data.get("started_at"),
            "completed_at": data.get("completed_at"),
            "can_proceed": (
                data.get("status") == InterviewSessionState.IN_PROGRESS.value and
                data.get("current_question_index", 0) < data.get("max_questions", MAX_QUESTIONS)
            ),
            "is_complete": (
                data.get("status") == InterviewSessionState.COMPLETED.value or
                len(answers.data) >= len(questions.data)
            )
        }


# Factory function
def create_interview_service(supabase_client: AsyncClient) -> InterviewSessionService:
    """Create an InterviewSessionService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured InterviewSessionService instance
    """
    return InterviewSessionService(supabase_client)
