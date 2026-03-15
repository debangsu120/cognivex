"""Analytics Router for Hiring Intelligence Endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from supabase import AsyncClient

from app.deps import get_supabase, get_current_user
from app.services.analytics_service import AnalyticsService
from app.services.skill_profile_service import SkillProfileService
from app.services.embedding_service import EmbeddingService
from app.services.integrity_service import IntegrityService
from app.services.cache_service import CacheService
from app.models.response import APIResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(supabase: AsyncClient = Depends(get_supabase)) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(supabase)


def get_skill_profile_service(supabase: AsyncClient = Depends(get_supabase)) -> SkillProfileService:
    """Get skill profile service instance."""
    return SkillProfileService(supabase)


def get_embedding_service(supabase: AsyncClient = Depends(get_supabase)) -> EmbeddingService:
    """Get embedding service instance."""
    return EmbeddingService(supabase)


def get_integrity_service(supabase: AsyncClient = Depends(get_supabase)) -> IntegrityService:
    """Get integrity service instance."""
    return IntegrityService(supabase)


def get_cache_service(supabase: AsyncClient = Depends(get_supabase)) -> CacheService:
    """Get cache service instance."""
    return CacheService(supabase)


# =============================================================================
# Hiring Intelligence Analytics
# =============================================================================

@router.get("/jobs/{job_id}/skill-gaps")
async def get_skill_gap_analysis(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get skill gap analysis for a job.

    Returns analysis of skill gaps based on candidate performance.
    """
    try:
        analysis = await analytics_service.get_skill_gap_analysis(job_id, current_user["id"])
        return APIResponse(data=analysis, message="Skill gap analysis retrieved")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/trends")
async def get_candidate_trends(
    job_id: str,
    days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get candidate performance trends over time.

    Returns daily/weekly performance metrics.
    """
    try:
        trends = await analytics_service.get_candidate_trend_analysis(job_id, days)
        return APIResponse(data=trends, message="Trend analysis retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/overview")
async def get_company_analytics(
    company_id: str,
    period_days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get overall company analytics.

    Returns aggregated metrics across all jobs.
    """
    try:
        analytics = await analytics_service.get_overall_company_analytics(company_id, period_days)
        return APIResponse(data=analytics, message="Company analytics retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/top-candidates")
async def get_top_candidates(
    company_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get top performing candidates across all jobs.

    Returns list of top candidates with scores.
    """
    try:
        candidates = await analytics_service.get_top_performing_candidates(company_id, limit)
        return APIResponse(data=candidates, message=f"Found {len(candidates)} top candidates")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Skill Profile Endpoints
# =============================================================================

@router.get("/users/{user_id}/skills")
async def get_user_skill_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    skill_service: SkillProfileService = Depends(get_skill_profile_service)
):
    """Get user's complete skill profile.

    Returns all skills with scores and trends.
    """
    try:
        profile = await skill_service.get_user_skill_profile(user_id)
        return APIResponse(data=profile, message="Skill profile retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/skills/top")
async def get_top_skills(
    user_id: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
    skill_service: SkillProfileService = Depends(get_skill_profile_service)
):
    """Get user's top performing skills.

    Returns top skills by score.
    """
    try:
        skills = await skill_service.get_top_skills(user_id, limit)
        return APIResponse(data=skills, message=f"Found {len(skills)} top skills")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/skills/improve")
async def get_skills_to_improve(
    user_id: str,
    threshold: float = Query(6.0, ge=0, le=10),
    current_user: dict = Depends(get_current_user),
    skill_service: SkillProfileService = Depends(get_skill_profile_service)
):
    """Get skills that need improvement.

    Returns skills below the score threshold.
    """
    try:
        skills = await skill_service.get_skills_needing_improvement(user_id, threshold)
        return APIResponse(data=skills, message=f"Found {len(skills)} skills to improve")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/skills/{skill}/trend")
async def get_skill_trend(
    user_id: str,
    skill: str,
    current_user: dict = Depends(get_current_user),
    skill_service: SkillProfileService = Depends(get_skill_profile_service)
):
    """Get trend for a specific skill.

    Returns improvement/decline over time.
    """
    try:
        trend = await skill_service.get_skill_trend(user_id, skill)
        if not trend:
            raise HTTPException(status_code=404, detail="Skill profile not found")
        return APIResponse(data=trend, message="Skill trend retrieved")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Semantic Skill Matching
# =============================================================================

@router.get("/skills/match")
async def match_skills(
    candidate_skills: str = Query(..., description="Comma-separated candidate skills"),
    job_skills: str = Query(..., description="Comma-separated job skills"),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Match candidate skills to job requirements semantically.

    Uses vector embeddings to find related skills even with different keywords.
    """
    try:
        candidate_list = [s.strip() for s in candidate_skills.split(",")]
        job_list = [s.strip() for s in job_skills.split(",")]

        result = await embedding_service.match_candidate_skills_to_job(
            candidate_skills=candidate_list,
            job_skills=job_list
        )

        return APIResponse(data=result, message="Skill matching complete")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills/similar")
async def find_similar_skills(
    skill: str,
    threshold: float = Query(0.7, ge=0, le=1),
    limit: int = Query(10, ge=1, le=20),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Find skills similar to the given skill.

    Uses semantic similarity to find related skills.
    """
    try:
        similar = await embedding_service.find_similar_skills(skill, threshold, limit)
        return APIResponse(data=similar, message=f"Found {len(similar)} similar skills")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills/embeddings")
async def store_skill_embeddings(
    skills: List[dict],
    current_user: dict = Depends(get_current_user),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Store embeddings for skills.

    Batch endpoint to pre-compute embeddings for common skills.
    """
    try:
        result = await embedding_service.batch_store_embeddings(skills)
        return APIResponse(data=result, message="Embeddings stored")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Interview Integrity
# =============================================================================

@router.get("/interviews/{interview_id}/integrity")
async def get_interview_integrity(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
    integrity_service: IntegrityService = Depends(get_integrity_service)
):
    """Get integrity analysis for an interview.

    Returns flags and integrity score.
    """
    try:
        analysis = await integrity_service.analyze_session_patterns(interview_id)
        return APIResponse(data=analysis, message="Integrity analysis retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interviews/{interview_id}/integrity/history")
async def get_integrity_history(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
    integrity_service: IntegrityService = Depends(get_integrity_service)
):
    """Get integrity history for an interview.

    Returns question-by-question integrity metrics.
    """
    try:
        history = await integrity_service.get_interview_integrity_history(interview_id)
        return APIResponse(data=history, message="Integrity history retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Cache Management
# =============================================================================

@router.get("/cache/stats")
async def get_cache_stats(
    current_user: dict = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Get AI cache statistics.

    Returns cache hit/miss info and token savings.
    """
    try:
        stats = await cache_service.get_cache_stats()
        return APIResponse(data=stats, message="Cache stats retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/cleanup")
async def cleanup_cache(
    current_user: dict = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Clean up expired cache entries.

    Returns number of entries removed.
    """
    try:
        removed = await cache_service.cleanup_expired()
        return APIResponse(data={"removed": removed}, message=f"Removed {removed} expired entries")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
