"""Dashboard Router for candidate and recruiter dashboard endpoints."""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from supabase import AsyncClient

from app.deps import get_supabase, get_current_user
from app.services.dashboard_service import DashboardService
from app.services.candidate_service import CandidateService
from app.services.recruiter_service import RecruiterService
from app.models.response import APIResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(supabase: AsyncClient = Depends(get_supabase)) -> DashboardService:
    """Get dashboard service instance."""
    return DashboardService(supabase)


def get_candidate_service(supabase: AsyncClient = Depends(get_supabase)) -> CandidateService:
    """Get candidate service instance."""
    return CandidateService(supabase)


def get_recruiter_service(supabase: AsyncClient = Depends(get_supabase)) -> RecruiterService:
    """Get recruiter service instance."""
    return RecruiterService(supabase)


@router.get("/candidate")
async def get_candidate_dashboard(
    current_user: dict = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    limit: int = Query(10, ge=1, le=50)
):
    """Get candidate dashboard data.

    Returns recommended jobs, available interviews, interview history,
    and statistics for the authenticated candidate.
    """
    dashboard_data = await dashboard_service.get_candidate_dashboard(
        candidate_id=current_user["id"],
        limit=limit
    )

    return APIResponse(
        data=dashboard_data,
        message="Candidate dashboard retrieved successfully"
    )


@router.get("/recruiter")
async def get_recruiter_dashboard(
    current_user: dict = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    company_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """Get recruiter dashboard data.

    Returns company info, active jobs, candidate counts, recent interviews,
    and top candidates for the authenticated recruiter.
    """
    dashboard_data = await dashboard_service.get_recruiter_dashboard(
        recruiter_id=current_user["id"],
        company_id=company_id,
        limit=limit
    )

    return APIResponse(
        data=dashboard_data,
        message="Recruiter dashboard retrieved successfully"
    )


@router.get("/candidate/profile")
async def get_candidate_profile(
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
    include_resume: bool = Query(True)
):
    """Get candidate profile with skills and resume.

    Returns the full profile including skills extracted from resume,
    completed interview count, and average score.
    """
    profile_data = await candidate_service.get_candidate_profile(
        candidate_id=current_user["id"],
        include_resume=include_resume
    )

    return APIResponse(
        data=profile_data,
        message="Candidate profile retrieved successfully"
    )


@router.get("/candidate/interviews")
async def get_candidate_interviews(
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get interview history for the candidate.

    Returns all interviews for the authenticated candidate,
    optionally filtered by status.
    """
    interviews = await candidate_service.get_candidate_interview_history(
        candidate_id=current_user["id"],
        status=status,
        limit=limit,
        offset=offset
    )

    return APIResponse(
        data=interviews,
        message="Interview history retrieved successfully"
    )


@router.get("/candidate/available")
async def get_available_interviews(
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
    limit: int = Query(10, ge=1, le=50)
):
    """Get available interviews for the candidate.

    Returns scheduled and ready interviews that the candidate
    can attend.
    """
    interviews = await candidate_service.get_available_interviews(
        candidate_id=current_user["id"],
        limit=limit
    )

    return APIResponse(
        data=interviews,
        message="Available interviews retrieved successfully"
    )


@router.get("/candidate/results")
async def get_past_results(
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
    limit: int = Query(10, ge=1, le=50)
):
    """Get past interview results for the candidate.

    Returns completed interview results with scores and recommendations.
    """
    results = await candidate_service.get_past_results(
        candidate_id=current_user["id"],
        limit=limit
    )

    return APIResponse(
        data=results,
        message="Past results retrieved successfully"
    )


@router.get("/candidate/skills")
async def get_candidate_skills(
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """Get candidate skill profile.

    Returns all skills extracted from resumes, categorized by type.
    """
    skills = await candidate_service.get_candidate_skill_profile(
        candidate_id=current_user["id"]
    )

    return APIResponse(
        data=skills,
        message="Skill profile retrieved successfully"
    )


@router.get("/candidate/trend")
async def get_performance_trend(
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
    limit: int = Query(10, ge=1, le=50)
):
    """Get candidate performance trend.

    Returns interview scores over time with running averages.
    """
    trend = await candidate_service.get_candidate_performance_trend(
        candidate_id=current_user["id"],
        limit=limit
    )

    return APIResponse(
        data=trend,
        message="Performance trend retrieved successfully"
    )


@router.get("/recruiter/company")
async def get_company_dashboard(
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    company_id: Optional[str] = Query(None)
):
    """Get company dashboard for recruiter.

    Returns company stats, job listings, and recent activity.
    """
    dashboard = await recruiter_service.get_company_dashboard(
        recruiter_id=current_user["id"],
        company_id=company_id
    )

    return APIResponse(
        data=dashboard,
        message="Company dashboard retrieved successfully"
    )


@router.get("/recruiter/jobs")
async def get_recruiter_jobs(
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    company_id: Optional[str] = Query(None),
    include_stats: bool = Query(True)
):
    """Get all jobs for recruiter with candidate stats.

    Returns all jobs posted by the recruiter's company with
    candidate counts and interview statistics.
    """
    jobs = await recruiter_service.get_all_jobs_with_candidates(
        recruiter_id=current_user["id"],
        company_id=company_id,
        include_stats=include_stats
    )

    return APIResponse(
        data=jobs,
        message="Jobs retrieved successfully"
    )


@router.get("/recruiter/candidates-summary")
async def get_candidates_summary(
    current_user: dict = Depends(get_current_user),
    recruiter_service: RecruiterService = Depends(get_recruiter_service),
    company_id: Optional[str] = Query(None)
):
    """Get candidates summary for recruiter.

    Returns summary of all candidates across recruiter's jobs.
    """
    summary = await recruiter_service.get_recruiter_candidates_summary(
        recruiter_id=current_user["id"],
        company_id=company_id
    )

    return APIResponse(
        data=summary,
        message="Candidates summary retrieved successfully"
    )


@router.get("/stats")
async def get_interview_statistics(
    current_user: dict = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    user_type: str = Query("candidate", pattern="^(candidate|recruiter)$")
):
    """Get interview statistics for current user.

    Returns statistics based on user type (candidate or recruiter).
    """
    stats = await dashboard_service.get_interview_statistics(
        user_id=current_user["id"],
        user_type=user_type
    )

    return APIResponse(
        data=stats,
        message="Statistics retrieved successfully"
    )
