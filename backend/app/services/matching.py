from typing import List, Dict, Optional, Any
from app.services.supabase import supabase_service
from app.services.groq import groq_service
from app.models.interview import CandidateMatch


def calculate_skill_match_score(
    candidate_skills: List[str],
    required_skills: List[str]
) -> Dict[str, Any]:
    """Calculate skill match score between candidate and job requirements.

    Formula: (matched_skills / required_skills) * 100

    Args:
        candidate_skills: List of candidate's skills
        required_skills: List of job's required skills

    Returns:
        Dictionary containing:
            - match_score: Percentage match (0-100)
            - matched_skills: List of skills matched
            - missing_skills: List of required skills not found
            - match_percentage: Formatted percentage string
    """
    if not required_skills:
        return {
            "match_score": 100,
            "matched_skills": candidate_skills,
            "missing_skills": [],
            "match_percentage": "100%"
        }

    if not candidate_skills:
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": required_skills,
            "match_percentage": "0%"
        }

    # Normalize skills for comparison (lowercase)
    candidate_skills_lower = {s.lower().strip(): s for s in candidate_skills}
    required_skills_lower = {s.lower().strip(): s for s in required_skills}

    # Find matched skills
    matched = []
    for skill_lower, skill_original in required_skills_lower.items():
        for cand_lower, cand_original in candidate_skills_lower.items():
            # Exact match
            if skill_lower == cand_lower:
                matched.append(cand_original)
                break
            # Partial match (one contains the other)
            elif skill_lower in cand_lower or cand_lower in skill_lower:
                matched.append(cand_original)
                break

    # Find missing skills
    matched_lower = {s.lower() for s in matched}
    missing = [s for s in required_skills if s.lower() not in matched_lower]

    # Calculate score
    match_score = (len(matched) / len(required_skills)) * 100 if required_skills else 100

    return {
        "match_score": round(match_score, 2),
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": f"{match_score:.0f}%"
    }


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
        limit: int = 10,
        use_ai: bool = True
    ) -> List[Dict]:
        """Find jobs that match a candidate's profile.

        Args:
            candidate_id: Candidate user ID
            limit: Maximum number of jobs to return
            use_ai: Whether to use AI for matching (slower but more accurate)

        Returns:
            List of jobs with match scores, sorted by match score
        """
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

            if use_ai:
                # Use AI for detailed matching
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
                    "skills_match_score": match_result.get("skills_match_score", 0),
                    "experience_match_score": match_result.get("experience_match_score", 0),
                    "matched_skills": match_result.get("matched_skills", []),
                    "missing_skills": match_result.get("missing_skills", [])
                })
            else:
                # Use fast formula-based matching
                skill_match = calculate_skill_match_score(
                    candidate_skills=candidate_skills,
                    required_skills=job_skills or []
                )

                matches.append({
                    "job": job,
                    "match_score": skill_match.get("match_score", 0),
                    "skills_match_score": skill_match.get("match_score", 0),
                    "experience_match_score": 0,  # Would need experience data
                    "matched_skills": skill_match.get("matched_skills", []),
                    "missing_skills": skill_match.get("missing_skills", [])
                })

        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches[:limit]

    async def find_matching_jobs_fast(
        self,
        candidate_skills: List[str],
        job_ids: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Find matching jobs using fast formula-based matching.

        This method uses a simple formula without AI, making it faster
        for quick candidate-job matching.

        Args:
            candidate_skills: List of candidate's skills
            job_ids: Optional list of job IDs to filter (None for all)
            limit: Maximum number of jobs to return

        Returns:
            List of jobs with match scores
        """
        # Get jobs
        if job_ids:
            jobs = []
            for job_id in job_ids:
                job = await self.supabase.get_job(job_id)
                if job:
                    jobs.append(job)
        else:
            jobs = await self.supabase.list_jobs(is_active=True)

        # Score each job using formula
        matches = []
        for job in jobs:
            job_skills = job.get("skills_required", [])

            skill_match = calculate_skill_match_score(
                candidate_skills=candidate_skills,
                required_skills=job_skills or []
            )

            matches.append({
                "job_id": job.get("id"),
                "job_title": job.get("title"),
                "company": job.get("companies", {}).get("name") if job.get("companies") else None,
                "match_score": skill_match.get("match_score", 0),
                "matched_skills": skill_match.get("matched_skills", []),
                "missing_skills": skill_match.get("missing_skills", []),
                "match_percentage": skill_match.get("match_percentage", "0%")
            })

        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches[:limit]


# Singleton instance
matching_service = MatchingService()
