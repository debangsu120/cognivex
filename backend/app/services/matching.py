from typing import List, Dict, Optional
from app.services.supabase import supabase_service
from app.services.groq import groq_service
from app.models.interview import CandidateMatch


class MatchingService:
    """Service for candidate-job matching."""

    def __init__(self):
        self.supabase = supabase_service

    async def match_candidate_to_job(
        self,
        candidate_id: str,
        job_id: str
    ) -> CandidateMatch:
        """Match a candidate to a job based on their profile and resume."""
        # Get candidate profile and resume
        profile = await self.supabase.get_profile(candidate_id)
        resumes = await self.supabase.get_user_resumes(candidate_id)
        resume = resumes[0] if resumes else None

        # Get job details
        job = await self.supabase.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        # Extract candidate skills
        candidate_skills = []
        if resume and resume.get("skills"):
            candidate_skills = resume.get("skills", [])
        candidate_experience = resume.get("experience_years", 0) if resume else 0

        # Get job requirements
        job_skills = job.get("skills_required", [])
        job_requirements = job.get("requirements", [])

        # Use AI to analyze match
        match_result = await groq_service.match_candidate_to_job(
            candidate_skills=candidate_skills,
            candidate_experience_years=candidate_experience,
            job_title=job.get("title", ""),
            job_requirements=job_requirements,
            job_skills_required=job_skills or []
        )

        # Determine matched and missing skills
        matched_skills = match_result.get("matched_skills", [])
        missing_skills = match_result.get("missing_skills", [])

        # Create candidate match object
        candidate_match = CandidateMatch(
            candidate_id=candidate_id,
            candidate_name=profile.get("full_name", "Unknown") if profile else "Unknown",
            candidate_email="",  # Would need to get from auth
            resume_id=resume.get("id") if resume else None,
            skills_match_score=match_result.get("skills_match_score", 0),
            experience_match_score=match_result.get("experience_match_score", 0),
            overall_match_score=match_result.get("overall_match_score", 0),
            matched_skills=matched_skills,
            missing_skills=missing_skills
        )

        return candidate_match

    async def find_matching_jobs(
        self,
        candidate_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Find jobs that match a candidate's profile."""
        # Get candidate resume
        resumes = await self.supabase.get_user_resumes(candidate_id)
        if not resumes:
            return []

        resume = resumes[0]
        candidate_skills = resume.get("skills", [])
        candidate_experience = resume.get("experience_years", 0)

        # Get all active jobs
        jobs = await self.supabase.list_jobs(is_active=True)

        # Score each job
        matches = []
        for job in jobs:
            job_skills = job.get("skills_required", [])
            job_requirements = job.get("requirements", [])

            match_result = await groq_service.match_candidate_to_job(
                candidate_skills=candidate_skills,
                candidate_experience_years=candidate_experience,
                job_title=job.get("title", ""),
                job_requirements=job_requirements,
                job_skills_required=job_skills or []
            )

            matches.append({
                "job": job,
                "match_score": match_result.get("overall_match_score", 0),
                "matched_skills": match_result.get("matched_skills", []),
                "missing_skills": match_result.get("missing_skills", [])
            })

        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches[:limit]


# Singleton instance
matching_service = MatchingService()
