from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from supabase import AsyncClient
from typing import List, Optional, Dict, Any
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
from app.services.interview_service import create_interview_service, InterviewSessionService
from app.services.speech_service import speech_service
from app.services.evaluation_service import create_evaluation_service
from app.services.scoring_service import create_scoring_service
from app.services.report_service import create_report_service

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


@router.post("/{interview_id}/start", response_model=APIResponse[InterviewResponse])
async def start_interview(
    interview_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Start an interview session.

    Transitions interview from READY to IN_PROGRESS state.
    """
    try:
        service: InterviewSessionService = create_interview_service(supabase)
        interview = await service.start_interview(interview_id)
        return APIResponse(data=interview, message="Interview started successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{interview_id}/questions", response_model=APIResponse[List[Dict[str, Any]]])
async def get_interview_questions(
    interview_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get all questions for an interview session.

    Returns all generated questions for the interview.
    """
    try:
        service: InterviewSessionService = create_interview_service(supabase)
        questions = await service.get_questions(interview_id)
        return APIResponse(data=questions, message=f"Found {len(questions)} questions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{interview_id}/next", response_model=APIResponse[Optional[Dict[str, Any]]])
async def get_next_question(
    interview_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get the next question in the interview.

    Returns the next question if available, or None if all questions completed.
    """
    try:
        service: InterviewSessionService = create_interview_service(supabase)
        question = await service.get_next_question(interview_id)

        if question is None:
            return APIResponse(
                data=None,
                message="No more questions available - interview may be complete"
            )

        return APIResponse(data=question, message="Next question retrieved")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{interview_id}/complete", response_model=APIResponse[InterviewResponse])
async def complete_interview(
    interview_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Complete an interview session manually.

    Ends the interview and generates final scores and feedback.
    """
    try:
        service: InterviewSessionService = create_interview_service(supabase)
        interview = await service.complete_interview(interview_id)
        return APIResponse(data=interview, message="Interview completed successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{interview_id}/state", response_model=APIResponse[Dict[str, Any]])
async def get_interview_state(
    interview_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get the current state of an interview session.

    Returns:
        - status: Current interview status
        - current_question_index: Current question number
        - total_questions: Total questions in interview
        - answered_questions: Number of answered questions
        - max_questions: Maximum allowed questions
        - duration_minutes: Interview duration limit
        - can_proceed: Whether more questions are available
        - is_complete: Whether interview is finished
    """
    try:
        service: InterviewSessionService = create_interview_service(supabase)
        state = await service.get_session_state(interview_id)
        return APIResponse(data=state, message="Interview state retrieved")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{interview_id}/audio", response_model=APIResponse[InterviewAnswerResponse])
async def upload_audio_answer(
    interview_id: str,
    question_id: str = Form(...),
    audio: UploadFile = File(...),
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Upload audio answer for a question and get it transcribed and evaluated.

    This endpoint:
    1. Accepts an audio file upload
    2. Transcribes the audio using STT (Deepgram/Whisper)
    3. Evaluates the answer using AI
    4. Saves the answer with transcript and evaluation to the database

    Returns the answer with score and feedback.
    """
    try:
        # Verify interview exists and is in progress
        interview = await supabase.table("interviews").select("*").eq("id", interview_id).execute()
        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        interview_data = interview.data[0]
        if interview_data.get("status") != "in_progress":
            raise HTTPException(status_code=400, detail="Interview is not in progress")

        # Verify question exists and belongs to this interview
        question = await supabase.table("interview_questions").select(
            "*, interviews(job_id, jobs(*))"
        ).eq("id", question_id).eq("interview_id", interview_id).execute()
        if not question.data:
            raise HTTPException(status_code=404, detail="Question not found in this interview")

        question_data = question.data[0]

        # Read audio file
        audio_data = await audio.read()

        # Check file size (max 10MB)
        if len(audio_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")

        # Analyze audio quality
        quality_analysis = await speech_service.analyze_audio_quality(audio_data)
        if not quality_analysis.get("is_suitable_for_stt"):
            raise HTTPException(
                status_code=400,
                detail=f"Audio quality too low. Duration: {quality_analysis.get('duration_seconds')}s"
            )

        # Transcribe audio
        try:
            transcription = await speech_service.transcribe_audio(audio_data=audio_data)
            transcript = transcription.get("transcript", "")
            confidence = transcription.get("confidence")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

        if not transcript:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        # Get job skills for evaluation
        interview_rel = question_data.get("interviews", {})
        job_data = interview_rel.get("jobs", {}) if isinstance(interview_rel, dict) else {}
        skills_required = job_data.get("skills_required", [])

        # Evaluate answer using AI
        try:
            evaluation = await groq_service.evaluate_answer(
                question=question_data.get("question_text", ""),
                answer=transcript,
                skills_required=skills_required
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

        # Upload audio to storage (Supabase Storage)
        audio_url = None
        try:
            file_extension = audio.filename.split(".")[-1] if "." in audio.filename else "wav"
            file_path = f"interviews/{interview_id}/answers/{question_id}/{datetime.utcnow().timestamp()}.{file_extension}"

            # Upload to Supabase Storage
            storage_response = await supabase.storage.from_("interview-audio").upload(
                file_path,
                audio_data,
                {"content-type": f"audio/{file_extension}"}
            )

            if storage_response.data:
                # Get public URL
                audio_url = supabase.storage.from_("interview-audio").get_public_url(file_path)
        except Exception as e:
            # Continue even if storage upload fails
            pass

        # Check if answer already exists
        existing = await supabase.table("interview_answers").select("*").eq("question_id", question_id).execute()

        answer_data = {
            "question_id": question_id,
            "answer_text": None,
            "audio_url": audio_url,
            "transcript": transcript,
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get("feedback", ""),
            "technical_accuracy": evaluation.get("technical_accuracy", 0),
            "communication_clarity": evaluation.get("communication_clarity", 0)
        }

        if existing.data:
            # Update existing answer
            response = await supabase.table("interview_answers").update(
                answer_data
            ).eq("id", existing.data[0]["id"]).execute()
            answer_id = existing.data[0]["id"]
        else:
            # Create new answer
            response = await supabase.table("interview_answers").insert(answer_data).execute()
            answer_id = response.data[0]["id"]

        # Check if all questions are answered
        await _check_and_complete_interview(supabase, interview_id)

        return APIResponse(
            data={
                **response.data[0],
                "transcription_confidence": confidence,
                "evaluation": evaluation
            },
            message="Audio answer submitted and evaluated successfully"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{interview_id}/transcript", response_model=APIResponse[List[Dict[str, Any]]])
async def get_transcript(
    interview_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get full transcript for an interview.

    Returns all questions and answers (transcripts or text) for the interview.
    """
    try:
        # Verify interview exists
        interview = await supabase.table("interviews").select("id").eq("id", interview_id).execute()
        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        # Get all answers with questions
        answers = await supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).order(
            "interview_questions.question_order"
        ).execute()

        transcript = []
        for answer in answers.data:
            question = answer.get("interview_questions", {})
            content = answer.get("transcript") or answer.get("answer_text")

            transcript.append({
                "question_number": question.get("question_order"),
                "question": question.get("question_text"),
                "category": question.get("category"),
                "skill": question.get("skill"),
                "answer": content,
                "audio_url": answer.get("audio_url"),
                "score": answer.get("score"),
                "answered_at": answer.get("created_at")
            })

        return APIResponse(
            data=transcript,
            message=f"Retrieved {len(transcript)} transcript entries"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{interview_id}/report", response_model=APIResponse[Dict[str, Any]])
async def get_interview_report(
    interview_id: str,
    report_type: str = "recruiter",
    include_transcript: bool = True,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get interview report.

    Args:
        interview_id: Interview ID
        report_type: Type of report - "candidate" or "recruiter"
        include_transcript: Whether to include full transcript in report

    Returns comprehensive interview report with scores, feedback, and optionally transcripts.
    """
    try:
        # Verify interview exists
        interview = await supabase.table("interviews").select("id").eq("id", interview_id).execute()
        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        # Create report service
        report_service = create_report_service(supabase)

        # Generate appropriate report
        if report_type == "candidate":
            report = await report_service.generate_candidate_report(
                interview_id,
                include_transcript=include_transcript
            )
        else:
            report = await report_service.generate_recruiter_report(
                interview_id,
                include_detailed_feedback=include_transcript
            )

        return APIResponse(data=report, message=f"{report_type} report generated successfully")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{interview_id}/evaluate", response_model=APIResponse[Dict[str, Any]])
async def evaluate_answer_text(
    interview_id: str,
    question_id: str,
    answer_text: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Evaluate a text answer without audio.

    This endpoint evaluates a typed answer without going through transcription.
    """
    try:
        # Verify interview exists
        interview = await supabase.table("interviews").select("*").eq("id", interview_id).execute()
        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        # Verify question exists
        question = await supabase.table("interview_questions").select(
            "*, interviews(job_id, jobs(*))"
        ).eq("id", question_id).eq("interview_id", interview_id).execute()
        if not question.data:
            raise HTTPException(status_code=404, detail="Question not found")

        question_data = question.data[0]

        # Get job skills
        interview_rel = question_data.get("interviews", {})
        job_data = interview_rel.get("jobs", {}) if isinstance(interview_rel, dict) else {}
        skills_required = job_data.get("skills_required", [])

        # Evaluate answer
        evaluation = await groq_service.evaluate_answer(
            question=question_data.get("question_text", ""),
            answer=answer_text,
            skills_required=skills_required
        )

        # Check if answer already exists
        existing = await supabase.table("interview_answers").select("*").eq("question_id", question_id).execute()

        answer_data = {
            "question_id": question_id,
            "answer_text": answer_text,
            "transcript": None,
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get("feedback", ""),
            "technical_accuracy": evaluation.get("technical_accuracy", 0),
            "communication_clarity": evaluation.get("communication_clarity", 0)
        }

        if existing.data:
            # Update existing
            response = await supabase.table("interview_answers").update(
                answer_data
            ).eq("id", existing.data[0]["id"]).execute()
        else:
            # Create new
            response = await supabase.table("interview_answers").insert(answer_data).execute()

        # Check if interview is complete
        await _check_and_complete_interview(supabase, interview_id)

        return APIResponse(
            data={
                "answer": response.data[0],
                "evaluation": evaluation
            },
            message="Answer evaluated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _check_and_complete_interview(supabase: AsyncClient, interview_id: str) -> None:
    """Check if all questions are answered and complete interview if so.

    Args:
        supabase: Supabase client
        interview_id: Interview ID
    """
    # Get total questions
    questions = await supabase.table("interview_questions").select(
        "id"
    ).eq("interview_id", interview_id).execute()

    # Get answered questions
    answers = await supabase.table("interview_answers").select(
        "id", "question_id"
    ).in_(
        "question_id",
        [q["id"] for q in questions.data]
    ).execute()

    # Get interview data
    interview = await supabase.table("interviews").select(
        "max_questions"
    ).eq("id", interview_id).execute()

    if not interview.data:
        return

    max_questions = interview.data[0].get("max_questions", 7)

    # If all questions answered or max reached, complete interview
    if len(answers.data) >= len(questions.data) or len(answers.data) >= max_questions:
        # Calculate final scores
        scoring_service = create_scoring_service(supabase)
        await scoring_service.recalculate_all_scores(interview_id)

        # Update interview status
        await supabase.table("interviews").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", interview_id).execute()
