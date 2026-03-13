"""Ranking Router for candidate ranking and comparison endpoints."""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from supabase import AsyncClient

from app.deps import get_supabase, get_current_user
from app.services.ranking_service import RankingService
from app.services.recruiter_service import RecruiterService
from app.models.response import APIResponse

router = APIRouter(prefix="/rankings", tags=["Rankings"])


def get_ranking_service(supabase: AsyncClient = Depends(get_supabase)) -> RankingService:
    """Get ranking service instance."""
    return RankingService(supabase)


def get_recruiter_service(supabase: AsyncClient = Depends(get_supabase)) -> RecruiterService:
    """Get recruiter service instance."""
    return RecruiterService(supabase)


@router.get("/jobs/{job_id}/candidates")
async def get_job_candidate_rankings(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    ranking_service: RankingService = Depends(get_ranking_service),
    ranking_type: str = Query(
        "interview",
        pattern="^(interview|skill|combined)$"
    ),
    limit: int = Query(20, ge=1, le=100),
    interview_weight: float = Query(0.6, ge=0, le=1),
    skill_weight: float = Query(0.4, ge=0, le=1)
):
    """Get ranked candidates for a job.

    Returns candidates ranked by interview score, skill match, or combined.
    This endpoint is for recruiters to view candidates for their jobs.
    """
    if ranking_type == "interview":
        rankings = await ranking_service.rank_candidates_by_interview_score(
            job_id=job_id,
            recruiter_id=current_user["id"],
            limit=limit
        )
    elif ranking_type == "skill":
        rankings = await ranking_service.rank_candidates_by_skill_match(
            job_id=job_id,
            recruiter_id=current_user["id"],
            limit=limit
        )
    else:  # combined
        rankings = await ranking_service.get_combined_ranking(
            job_id=job_id,
            recruiter_id=current_user["id"],
            interview_weight=interview_weight,
            skill_weight=skill_weight,
            limit=limit
        )

    return APIResponse(
        data=rankings,
        message=f"Candidates ranked by {ranking_type} score"
    )


@router.get("/jobs/{job_id}/candidates/ranked")
async def get_ranked_candidates(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    limit: int = Query(20, ge=1, le=100)
):
    """Get ranked candidates for a job (completed interviews only).

    Returns candidates ranked by overall interview score.
    This is a simplified endpoint for quick access.
    """
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
        message="Ranked candidates retrieved successfully"
    )


@router.get("/jobs/{job_id}/candidates/skill-match")
async def get_skill_matched_candidates(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    ranking_service: RankingService = Depends(get_ranking_service),
    limit: int = Query(20, ge=1, le=100)
):
    """Get candidates ranked by skill match.

    Returns candidates ranked by how well their skills match
    the job requirements.
    """
    rankings = await ranking_service.rank_candidates_by_skill_match(
        job_id=job_id,
        recruiter_id=current_user["id"],
        limit=limit
    )

    return APIResponse(
        data=rankings,
        message="Candidates ranked by skill match"
    )


@router.get("/jobs/{job_id}/candidates/combined")
async def get_combined_rankings(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    ranking_service: RankingService = Depends(get_ranking_service),
    interview_weight: float = Query(0.6, ge=0, le=1),
    skill_weight: float = Query(0.4, ge=0, le=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get candidates with combined ranking.

    Returns candidates ranked by a weighted combination of
    interview score and skill match.
    """
    rankings = await ranking_service.get_combined_ranking(
        job_id=job_id,
        recruiter_id=current_user["id"],
        interview_weight=interview_weight,
        skill_weight=skill_weight,
        limit=limit
    )

    return APIResponse(
        data=rankings,
        message="Combined rankings retrieved successfully"
    )


@router.get("/jobs/{job_id}/compare")
async def compare_candidates(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    ranking_service: RankingService = Depends(get_ranking_service),
    candidate_ids: List[str] = Query(...)
):
    """Compare multiple candidates for a job.

    Returns detailed comparison of selected candidates including
    scores, skill matches, and recommendations.
    """
    if len(candidate_ids) < 2:
        return APIResponse(
            data=None,
            error="At least 2 candidates required for comparison",
            success=False
        )

    comparison = await ranking_service.compare_candidates(
        job_id=job_id,
        candidate_ids=candidate_ids,
        recruiter_id=current_user["id"]
    )

    return APIResponse(
        data=comparison,
        message="Candidates compared successfully"
    )


@router.get("/candidates/{candidate_id}/jobs")
async def get_candidate_job_rankings(
    candidate_id: str,
    current_user: dict = Depends(get_current_user),
    ranking_service: RankingService = Depends(get_ranking_service),
    limit: int = Query(10, ge=1, le=50)
):
    """Get candidate's rankings across jobs.

    Returns the candidate's rank in each job they've interviewed for.
    This shows how they compare to other candidates.
    """
    # Only allow candidates to view their own rankings,
    # or recruiters to view any candidate's rankings
    is_own_profile = current_user["id"] == candidate_id

    # For now, allow any authenticated user to view
    # In production, add proper authorization checks

    rankings = await ranking_service.get_candidate_rankings_across_jobs(
        candidate_id=candidate_id,
        limit=limit
    )

    return APIResponse(
        data={
            "candidate_id": candidate_id,
            "rankings": rankings
        },
        message="Candidate job rankings retrieved successfully"
    )


@router.get("/candidates/{candidate_id}/rankings")
async def get_candidate_rankings(
    candidate_id: str,
    current_user: dict = Depends(get_current_user),
    ranking_service: RankingService = Depends(get_ranking_service),
    job_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Get rankings for a specific candidate.

    Returns ranking information for a candidate, either across
    all jobs or for a specific job.
    """
    # Get the candidate's interviews
    from app.deps import get_supabase
    supabase = await get_supabase()

    if job_id:
        # Get ranking for specific job
        from app.services.supabase import supabase_service
        job = await supabase_service.get_job(job_id)

        if not job:
            return APIResponse(
                data=None,
                error="Job not found",
                success=False
            )

        # Get this candidate's interview for the job
        interviews = await supabase.table("interviews").select(
            "*, interview_scores(*)"
        ).eq("job_id", job_id).eq("candidate_id", candidate_id).eq(
            "status", "completed"
        ).execute()

        if not interviews.data:
            return APIResponse(
                data={
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "rank": None,
                    "message": "No completed interview found"
                },
                message="No interview found"
            )

        # Calculate rank
        all_interviews = await supabase.table("interviews").select(
            "id"
        ).eq("job_id", job_id).eq("status", "completed").execute()

        higher_scores = 0
        candidate_score = interviews.data[0].get("interview_scores", [{}])[0].get("overall_score", 0)

        for interview in all_interviews.data:
            if interview["id"] == interviews.data[0]["id"]:
                continue

            other_score_data = await supabase.table("interview_scores").select(
                "overall_score"
            ).eq("interview_id", interview["id"]).execute()

            if other_score_data.data and other_score_data.data[0].get("overall_score"):
                if other_score_data.data[0]["overall_score"] > candidate_score:
                    higher_scores += 1

        rank = higher_scores + 1

        # Get profile
        profile = await supabase_service.get_profile(candidate_id)

        return APIResponse(
            data={
                "candidate_id": candidate_id,
                "candidate_name": profile.get("full_name") if profile else None,
                "job_id": job_id,
                "job_title": job.get("title") if job else None,
                "rank": rank,
                "total_candidates": len(all_interviews.data),
                "score": candidate_score
            },
            message="Candidate ranking retrieved successfully"
        )
    else:
        # Get rankings across all jobs
        rankings = await ranking_service.get_candidate_rankings_across_jobs(
            candidate_id=candidate_id,
            limit=limit
        )

        return APIResponse(
            data={
                "candidate_id": candidate_id,
                "rankings": rankings
            },
            message="Candidate rankings retrieved successfully"
        )


@router.post("/jobs/{job_id}/manage")
async def manage_job_posting(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    action: str = Query(..., pattern="^(activate|deactivate|update)$")
):
    """Manage job posting status.

    Allows recruiters to activate, deactivate, or update their job postings.
    """
    try:
        result = await recruiter_service.manage_job_posting(
            job_id=job_id,
            recruiter_id=current_user["id"],
            action=action
        )

        return APIResponse(
            data=result,
            message=f"Job {action}d successfully"
        )
    except ValueError as e:
        return APIResponse(
            data=None,
            error=str(e),
            success=False
        )
