from fastapi import APIRouter, Depends, HTTPException
from supabase import AsyncClient
from typing import List, Optional
from datetime import datetime
from app.deps import get_supabase, get_current_user
from app.models.interview import (
    InterviewCreate,
    InterviewUpdate,
    InterviewResponse,
    InterviewAnswerCreate,
    InterviewAnswerResponse,
    InterviewScoreResponse
)
from app.models.response import APIResponse
from app.services.groq import groq_service
from app.services.supabase import supabase_service

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", response_model=APIResponse[InterviewResponse])
async def create_interview(
    interview_data: InterviewCreate,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Create a new interview session."""
    try:
        # Verify job exists
        job = await supabase.table("jobs").select("*").eq("id", interview_data.job_id).execute()
        if not job.data:
            raise HTTPException(status_code=404, detail="Job not found")

        interview = interview_data.model_dump()
        interview["created_by"] = current_user.id

        response = await supabase.table("interviews").insert(interview).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create interview")

        interview_id = response.data[0]["id"]

        # Generate interview questions using AI
        job_data = job.data[0]
        questions = await groq_service.generate_interview_questions(
            job_title=job_data.get("title", ""),
            job_description=job_data.get("description", ""),
            skills_required=job_data.get("skills_required", []),
            difficulty=interview_data.difficulty.value,
            count=5
        )

        # Save questions to database
        for i, q in enumerate(questions):
            await supabase.table("interview_questions").insert({
                "interview_id": interview_id,
                "question_text": q.get("question", ""),
                "question_order": i + 1,
                "category": q.get("category"),
                "difficulty": q.get("difficulty")
            }).execute()

        # Get the full interview with questions
        full_interview = await supabase.table("interviews").select("*, jobs(*), interview_questions(*)").eq("id", interview_id).execute()

        return APIResponse(data=full_interview.data[0], message="Interview created successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse[List[InterviewResponse]])
async def list_interviews(
    candidate_id: Optional[str] = None,
    job_id: Optional[str] = None,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """List interviews for the current user."""
    try:
        query = supabase.table("interviews").select("*, jobs(*)")
        if candidate_id:
            query = query.eq("candidate_id", candidate_id)
        if job_id:
            query = query.eq("job_id", job_id)

        response = await query.execute()

        return APIResponse(data=response.data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{interview_id}", response_model=APIResponse[InterviewResponse])
async def get_interview(
    interview_id: str,
    supabase: AsyncClient = Depends(get_supabase)
):
    """Get an interview by ID."""
    try:
        response = await supabase.table("interviews").select("*, jobs(*), interview_questions(*), interview_answers(*), interview_scores(*)").eq("id", interview_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        return APIResponse(data=response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{interview_id}", response_model=APIResponse[InterviewResponse])
async def update_interview(
    interview_id: str,
    interview_data: InterviewUpdate,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Update an interview."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in interview_data.model_dump().items() if v is not None}

        response = await supabase.table("interviews").update(update_data).eq("id", interview_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        return APIResponse(data=response.data[0], message="Interview updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{interview_id}/answer", response_model=APIResponse[InterviewAnswerResponse])
async def submit_answer(
    interview_id: str,
    answer_data: InterviewAnswerCreate,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Submit an answer to an interview question."""
    try:
        # Verify interview exists
        interview = await supabase.table("interviews").select("*").eq("id", interview_id).execute()
        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        # Verify question exists
        question = await supabase.table("interview_questions").select("*").eq("id", answer_data.question_id).execute()
        if not question.data:
            raise HTTPException(status_code=404, detail="Question not found")

        # Get job to find required skills
        job = await supabase.table("jobs").select("skills_required").eq("id", interview.data[0]["job_id"]).execute()
        skills_required = job.data[0].get("skills_required", []) if job.data else []

        # Evaluate answer using AI
        evaluation = await groq_service.evaluate_answer(
            question=question.data[0]["question_text"],
            answer=answer_data.answer_text or "",
            skills_required=skills_required
        )

        # Check if answer already exists
        existing_answer = await supabase.table("interview_answers").select("*").eq("question_id", answer_data.question_id).execute()

        answer = {
            "question_id": answer_data.question_id,
            "answer_text": answer_data.answer_text,
            "audio_url": answer_data.audio_url,
            "transcript": answer_data.transcript,
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get("feedback", "")
        }

        if existing_answer.data:
            # Update existing answer
            response = await supabase.table("interview_answers").update(answer).eq("id", existing_answer.data[0]["id"]).execute()
        else:
            # Create new answer
            response = await supabase.table("interview_answers").insert(answer).execute()

        # Check if all questions are answered
        questions = await supabase.table("interview_questions").select("id").eq("interview_id", interview_id).execute()
        answers = await supabase.table("interview_answers").select("question_id").eq("question_id", "in", [q["id"] for q in questions.data]).execute()

        # If all questions answered, generate overall feedback
        if len(answers.data) >= len(questions.data):
            all_answers = await supabase.table("interview_answers").select("*, interview_questions(*)").eq("interview_questions.interview_id", interview_id).execute()

            job_data = job.data[0] if job.data else {}
            feedback = await groq_service.generate_overall_feedback(
                interview_answers=[
                    {"question": a.get("interview_questions", {}).get("question_text", ""), "answer": a.get("answer_text", ""), "score": a.get("score", 0)}
                    for a in all_answers.data
                ],
                job_title=job_data.get("title", "Position")
            )

            # Update or create interview score
            existing_score = await supabase.table("interview_scores").select("*").eq("interview_id", interview_id).execute()

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
                await supabase.table("interview_scores").update(score_data).eq("interview_id", interview_id).execute()
            else:
                await supabase.table("interview_scores").insert(score_data).execute()

            # Update interview status
            await supabase.table("interviews").update({"status": "completed"}).eq("id", interview_id).execute()

        return APIResponse(data=response.data[0], message="Answer submitted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{interview_id}/score", response_model=APIResponse[InterviewScoreResponse])
async def get_interview_score(
    interview_id: str,
    supabase: AsyncClient = Depends(get_supabase)
):
    """Get the score for an interview."""
    try:
        response = await supabase.table("interview_scores").select("*").eq("interview_id", interview_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Score not found")

        return APIResponse(data=response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
