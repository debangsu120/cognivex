"""Recruiter Router for recruiter-specific operations."""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from supabase import AsyncClient

from app.deps import get_supabase, get_current_user
from app.services.recruiter_service import RecruiterService
from app.services.ranking_service import RankingService
from app.models.response import APIResponse

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


def get_recruiter_service(supabase: AsyncClient = Depends(get_supabase)) -> RecruiterService:
    """Get recruiter service instance."""
    return RecruiterService(supabase)


def get_ranking_service(supabase: AsyncClient = Depends(get_supabase)) -> RankingService:
    """Get ranking service instance."""
    return RankingService(supabase)


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@router.get("/dashboard")
async def get_recruiter_dashboard(
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    company_id: Optional[str] = None
):
    """Get recruiter dashboard with company stats and overview.

    Returns company information, job counts, candidate counts,
    and recent activity.
    """
    try:
        dashboard = await recruiter_service.get_company_dashboard(
            recruiter_id=current_user["id"],
            company_id=company_id
        )
        return APIResponse(data=dashboard, message="Dashboard retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_recruiter_jobs(
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    company_id: Optional[str] = None,
    include_stats: bool = True
):
    """Get all jobs for recruiter with candidate stats.

    Returns list of jobs with candidate counts and average scores.
    """
    try:
        jobs = await recruiter_service.get_all_jobs_with_candidates(
            recruiter_id=current_user["id"],
            company_id=company_id,
            include_stats=include_stats
        )
        return APIResponse(data=jobs, message=f"Found {len(jobs)} jobs")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Candidate Management Endpoints
# =============================================================================

@router.get("/jobs/{job_id}/candidates")
async def get_job_candidates(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get candidates for a specific job.

    Returns list of candidates who have taken interviews
    for the specified job.
    """
    try:
        candidates = await recruiter_service.get_candidates_for_job(
            job_id=job_id,
            recruiter_id=current_user["id"],
            status=status,
            limit=limit,
            offset=offset
        )
        return APIResponse(data=candidates, message=f"Found {len(candidates)} candidates")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/candidates/ranked")
async def get_ranked_candidates(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    limit: int = Query(20, ge=1, le=100)
):
    """Get ranked candidates for a job.

    Returns candidates sorted by interview score (highest first).
    """
    try:
        rankings = await recruiter_service.get_job_ranking(
            job_id=job_id,
            recruiter_id=current_user["id"],
            limit=limit
        )
        return APIResponse(
            data={
                "job_id": job_id,
                "candidates": rankings
            },
            message=f"Found {len(rankings)} ranked candidates"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Shortlisting Endpoints
# =============================================================================

@router.post("/candidates/{interview_id}/status")
async def update_candidate_status(
    interview_id: str,
    status: str = Query(..., pattern="^(pending|shortlisted|rejected|offered)$"),
    current_user: dict = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_supabase)
):
    """Update candidate status (shortlist, reject, offer).

    Updates the status of a candidate for a specific interview.
    Valid statuses: pending, shortlisted, rejected, offered
    """
    try:
        # Verify interview exists and belongs to recruiter's job
        interview = await supabase.table("interviews").select(
            "*, jobs(company_id)"
        ).eq("id", interview_id).execute()

        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        interview_data = interview.data[0]
        job = interview_data.get("jobs", {})

        # Verify recruiter has access to this job
        companies = await supabase.table("companies").select("id").eq(
            "owner_id", current_user["id"]
        ).execute()

        company_ids = [c["id"] for c in companies.data]
        if job.get("company_id") not in company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this job")

        # Update status
        updated = await supabase.table("interviews").update({
            "candidate_status": status,
            "updated_at": "now()"
        }).eq("id", interview_id).execute()

        return APIResponse(
            data=updated.data[0] if updated.data else None,
            message=f"Candidate status updated to {status}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidates/{interview_id}/status")
async def get_candidate_status(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_supabase)
):
    """Get candidate status for an interview.

    Returns the current status of a candidate.
    """
    try:
        interview = await supabase.table("interviews").select(
            "id, candidate_status, status"
        ).eq("id", interview_id).execute()

        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        return APIResponse(
            data=interview.data[0],
            message="Status retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/shortlisted")
async def get_shortlisted_candidates(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service)
):
    """Get shortlisted candidates for a job.

    Returns all candidates who have been shortlisted for the job.
    """
    try:
        candidates = await recruiter_service.get_candidates_for_job(
            job_id=job_id,
            recruiter_id=current_user["id"],
            status=None,  # We'll filter after getting
            limit=100,
            offset=0
        )

        # Filter shortlisted
        shortlisted = [c for c in candidates if c.get("status") == "shortlisted"]

        return APIResponse(
            data=shortlisted,
            message=f"Found {len(shortlisted)} shortlisted candidates"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Analytics Endpoints
# =============================================================================

@router.get("/jobs/{job_id}/analytics")
async def get_job_analytics(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    ranking_service: RankingService = Depends(get_ranking_service)
):
    """Get analytics for a specific job.

    Returns:
    - Average scores (overall, technical, communication)
    - Top candidates
    - Skill gap analysis
    - Interview completion rate
    """
    try:
        # Get job info
        from app.services.supabase import supabase_service
        job = await supabase_service.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Verify access
        companies = await recruiter_service.supabase.table("companies").select(
            "id"
        ).eq("owner_id", current_user["id"]).execute()

        company_ids = [c["id"] for c in companies.data]
        if job.get("company_id") not in company_ids:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get all completed interviews
        interviews = await recruiter_service.supabase.table("interviews").select(
            "id"
        ).eq("job_id", job_id).eq("status", "completed").execute()

        interview_ids = [i["id"] for i in interviews.data]

        if not interview_ids:
            return APIResponse(
                data={
                    "job_id": job_id,
                    "job_title": job.get("title"),
                    "total_completed": 0,
                    "average_scores": {
                        "overall": None,
                        "technical": None,
                        "communication": None,
                        "problem_solving": None
                    },
                    "top_candidates": [],
                    "skill_gaps": [],
                    "completion_rate": 0
                },
                message="No completed interviews yet"
            )

        # Get scores
        scores = await recruiter_service.supabase.table("interview_scores").select(
            "*"
        ).in_("interview_id", interview_ids).execute()

        # Calculate averages
        if scores.data:
            overall_scores = [s["overall_score"] for s in scores.data if s.get("overall_score")]
            technical_scores = [s["technical_score"] for s in scores.data if s.get("technical_score")]
            communication_scores = [s["communication_score"] for s in scores.data if s.get("communication_score")]
            problem_solving_scores = [s["problem_solving_score"] for s in scores.data if s.get("problem_solving_score")]

            avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else None
            avg_technical = sum(technical_scores) / len(technical_scores) if technical_scores else None
            avg_communication = sum(communication_scores) / len(communication_scores) if communication_scores else None
            avg_problem_solving = sum(problem_solving_scores) / len(problem_solving_scores) if problem_solving_scores else None
        else:
            avg_overall = avg_technical = avg_communication = avg_problem_solving = None

        # Get top 5 candidates
        rankings = await ranking_service.rank_candidates_by_interview_score(
            job_id=job_id,
            recruiter_id=current_user["id"],
            limit=5
        )

        # Calculate completion rate
        total_interviews = await recruiter_service.supabase.table("interviews").select(
            "id", count="exact"
        ).eq("job_id", job_id).execute()

        completed_count = len(interview_ids)
        total_count = total_interviews.count or 0
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0

        # Get job skills for gap analysis
        job_skills = job.get("skills_required", [])

        return APIResponse(
            data={
                "job_id": job_id,
                "job_title": job.get("title"),
                "total_completed": completed_count,
                "average_scores": {
                    "overall": round(avg_overall, 1) if avg_overall else None,
                    "technical": round(avg_technical, 1) if avg_technical else None,
                    "communication": round(avg_communication, 1) if avg_communication else None,
                    "problem_solving": round(avg_problem_solving, 1) if avg_problem_solving else None
                },
                "top_candidates": rankings[:5],
                "skill_gaps": job_skills,  # Placeholder for actual skill analysis
                "completion_rate": round(completion_rate, 1)
            },
            message="Analytics retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/overview")
async def get_overview_analytics(
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service)
):
    """Get overview analytics across all recruiter's jobs.

    Returns aggregated stats across all jobs.
    """
    try:
        # Get summary
        summary = await recruiter_service.get_recruiter_candidates_summary(
            recruiter_id=current_user["id"]
        )

        # Get all jobs with stats
        jobs = await recruiter_service.get_all_jobs_with_candidates(
            recruiter_id=current_user["id"],
            include_stats=True
        )

        # Calculate overall averages
        total_candidates = summary.get("total_candidates", 0)
        completed_interviews = summary.get("candidates_by_status", {}).get("completed", 0)

        avg_scores = []
        for job in jobs:
            stats = job.get("stats", {})
            if stats.get("average_score"):
                avg_scores.append(stats["average_score"])

        overall_avg = sum(avg_scores) / len(avg_scores) if avg_scores else None

        return APIResponse(
            data={
                "total_candidates": total_candidates,
                "total_completed_interviews": completed_interviews,
                "average_score": round(overall_avg, 1) if overall_avg else None,
                "candidates_by_status": summary.get("candidates_by_status", {}),
                "jobs_count": len(jobs),
                "active_jobs": sum(1 for j in jobs if j.get("status") == "active")
            },
            message="Overview analytics retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Candidate Report Endpoints
# =============================================================================

@router.get("/candidates/{interview_id}/report")
async def get_candidate_report(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_supabase)
):
    """Get detailed interview report for a candidate.

    Returns full interview evaluation including:
    - Candidate info
    - Job info
    - Overall score
    - Skill breakdown
    - Strengths and weaknesses
    - Transcript
    """
    try:
        # Get interview with related data
        interview = await supabase.table("interviews").select(
            "*, jobs(*), profiles!interviews_candidate_id_fkey(*), interview_scores(*)"
        ).eq("id", interview_id).execute()

        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview not found")

        interview_data = interview.data[0]
        job = interview_data.get("jobs", {})
        profile = interview_data.get("profiles", {})
        scores = interview_data.get("interview_scores", [{}])[0] if interview_data.get("interview_scores") else {}

        # Verify access
        companies = await supabase.table("companies").select("id").eq(
            "owner_id", current_user["id"]
        ).execute()

        company_ids = [c["id"] for c in companies.data]
        if job.get("company_id") not in company_ids:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get transcript
        questions = await supabase.table("interview_questions").select(
            "*"
        ).eq("interview_id", interview_id).order("question_order").execute()

        answers = await supabase.table("interview_answers").select(
            "*"
        ).in_(
            "question_id",
            [q["id"] for q in questions.data]
        ).execute()

        # Build transcript
        transcript = []
        for q in questions.data:
            answer = next((a for a in answers.data if a.get("question_id") == q["id"]), None)
            transcript.append({
                "question_number": q.get("question_order"),
                "question": q.get("question_text"),
                "category": q.get("category"),
                "skill": q.get("skill"),
                "answer": answer.get("answer_text") or answer.get("transcript") if answer else None,
                "score": answer.get("score") if answer else None,
                "feedback": answer.get("feedback") if answer else None
            })

        # Build report
        report = {
            "candidate": {
                "name": profile.get("full_name"),
                "email": profile.get("email"),
                "avatar": profile.get("avatar_url")
            },
            "job": {
                "title": job.get("title"),
                "company": job.get("company_id"),  # Could fetch company name
                "location": job.get("location")
            },
            "interview": {
                "status": interview_data.get("status"),
                "difficulty": interview_data.get("difficulty"),
                "duration_minutes": interview_data.get("duration_minutes"),
                "completed_at": interview_data.get("completed_at")
            },
            "overall_score": scores.get("overall_score"),
            "skill_breakdown": {
                "technical": scores.get("technical_score"),
                "communication": scores.get("communication_score"),
                "problem_solving": scores.get("problem_solving_score"),
                "cultural_fit": scores.get("cultural_fit_score")
            },
            "strengths": scores.get("strengths", []),
            "weaknesses": scores.get("weaknesses", []),
            "summary": scores.get("summary"),
            "recommendation": scores.get("recommendation"),
            "transcript": transcript,
            "candidate_status": interview_data.get("candidate_status", "pending")
        }

        return APIResponse(data=report, message="Report retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
