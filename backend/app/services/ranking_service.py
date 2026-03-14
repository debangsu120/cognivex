"""Ranking Service for ranking candidates based on interview scores and skill matches."""

from typing import Dict, List, Any, Optional
from supabase import AsyncClient

from app.services.supabase import supabase_service
from app.services.matching import calculate_skill_match_score


class RankingService:
    """Service for ranking candidates."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client
        """
        self.supabase = supabase_client

    async def rank_candidates_by_interview_score(
        self,
        job_id: str,
        recruiter_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Rank candidates by interview score for a specific job.

        Args:
            job_id: Job ID
            recruiter_id: Recruiter user ID (for authorization)
            limit: Maximum number of candidates to return

        Returns:
            Ranked candidates list
        """
        # Verify access
        await self._verify_job_access(job_id, recruiter_id)

        # Get completed interviews for this job
        interviews = await self.supabase.table("interviews").select(
            "*, profiles!interviews_candidate_id_fkey(*), interview_scores(*)"
        ).eq("job_id", job_id).eq("status", "completed").execute()

        # Get job details
        job = await supabase_service.get_job(job_id)
        required_skills = job.get("skills_required", []) if job else []

        # Build rankings
        candidates = []
        for interview in interviews.data:
            profile = interview.get("profiles")
            scores = interview.get("interview_scores", [{}])[0] if interview.get("interview_scores") else {}

            if not scores.get("overall_score"):
                continue

            candidate_data = {
                "interview_id": interview.get("id"),
                "candidate_id": interview.get("candidate_id"),
                "candidate_name": profile.get("full_name") if profile else "Unknown",
                "candidate_email": profile.get("email") if profile else None,
                "candidate_avatar": profile.get("avatar_url") if profile else None,
                "overall_score": scores.get("overall_score"),
                "technical_score": scores.get("technical_score"),
                "communication_score": scores.get("communication_score"),
                "problem_solving_score": scores.get("problem_solving_score"),
                "cultural_fit_score": scores.get("cultural_fit_score"),
                "recommendation": scores.get("recommendation"),
                "strengths": scores.get("strengths", []),
                "weaknesses": scores.get("weaknesses", []),
                "summary": scores.get("summary"),
                "completed_at": interview.get("completed_at")
            }

            candidates.append(candidate_data)

        # Sort by overall score
        candidates.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        # Add ranks
        ranked_candidates = []
        for i, c in enumerate(candidates):
            c["rank"] = i + 1
            ranked_candidates.append(c)

        return {
            "job_id": job_id,
            "job_title": job.get("title") if job else None,
            "total_candidates": len(ranked_candidates),
            "candidates": ranked_candidates[:limit]
        }

    async def rank_candidates_by_skill_match(
        self,
        job_id: str,
        recruiter_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Rank candidates by skill match for a specific job.

        Args:
            job_id: Job ID
            recruiter_id: Recruiter user ID (for authorization)
            limit: Maximum number of candidates to return

        Returns:
            Ranked candidates by skill match
        """
        # Verify access
        await self._verify_job_access(job_id, recruiter_id)

        # Get job details
        job = await supabase_service.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        required_skills = job.get("skills_required", [])

        # Get all candidates who have applied/interviewed for this job
        interviews = await self.supabase.table("interviews").select(
            "candidate_id"
        ).eq("job_id", job_id).execute()

        candidate_ids = list(set(
            i["candidate_id"] for i in interviews.data if i.get("candidate_id")
        ))

        # Calculate skill match for each candidate
        candidates = []
        for candidate_id in candidate_ids:
            # Get candidate's resume/skills
            resumes = await supabase_service.get_user_resumes(candidate_id)
            if not resumes:
                continue

            resume = resumes[0]
            candidate_skills = resume.get("skills", [])

            # Calculate skill match
            match_result = calculate_skill_match_score(
                candidate_skills=candidate_skills,
                required_skills=required_skills
            )

            # Get candidate profile
            profile = await supabase_service.get_profile(candidate_id)

            candidates.append({
                "candidate_id": candidate_id,
                "candidate_name": profile.get("full_name") if profile else "Unknown",
                "candidate_avatar": profile.get("avatar_url") if profile else None,
                "skill_match_score": match_result.get("match_score"),
                "matched_skills": match_result.get("matched_skills", []),
                "missing_skills": match_result.get("missing_skills", []),
                "match_percentage": match_result.get("match_percentage"),
                "total_candidate_skills": len(candidate_skills)
            })

        # Sort by skill match score
        candidates.sort(key=lambda x: x.get("skill_match_score", 0), reverse=True)

        # Add ranks
        ranked_candidates = []
        for i, c in enumerate(candidates):
            c["rank"] = i + 1
            ranked_candidates.append(c)

        return {
            "job_id": job_id,
            "job_title": job.get("title"),
            "required_skills": required_skills,
            "total_candidates": len(ranked_candidates),
            "candidates": ranked_candidates[:limit]
        }

    async def get_combined_ranking(
        self,
        job_id: str,
        recruiter_id: str,
        interview_weight: float = 0.6,
        skill_weight: float = 0.4,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get combined ranking based on both interview score and skill match.

        The combined score is calculated as:
        combined_score = (interview_score * interview_weight) + (skill_match_score * skill_weight)

        Args:
            job_id: Job ID
            recruiter_id: Recruiter user ID (for authorization)
            interview_weight: Weight for interview score (0-1)
            skill_weight: Weight for skill match (0-1)
            limit: Maximum number of candidates to return

        Returns:
            Combined rankings
        """
        # Verify access
        await self._verify_job_access(job_id, recruiter_id)

        # Normalize weights
        total_weight = interview_weight + skill_weight
        interview_weight = interview_weight / total_weight
        skill_weight = skill_weight / total_weight

        # Get job details
        job = await supabase_service.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        required_skills = job.get("skills_required", [])

        # Get interviews with scores
        interviews = await self.supabase.table("interviews").select(
            "*, profiles!interviews_candidate_id_fkey(*), interview_scores(*)"
        ).eq("job_id", job_id).eq("status", "completed").execute()

        # Get all unique candidates
        candidate_ids = list(set(
            i.get("candidate_id") for i in interviews.data if i.get("candidate_id")
        ))

        # Build combined rankings
        combined_candidates = []

        for candidate_id in candidate_ids:
            # Find this candidate's interview
            candidate_interview = None
            for i in interviews.data:
                if i.get("candidate_id") == candidate_id:
                    candidate_interview = i
                    break

            # Get interview score
            interview_score = 0
            if candidate_interview and candidate_interview.get("interview_scores"):
                interview_score = candidate_interview["interview_scores"][0].get("overall_score", 0) or 0

            # Get skill match score
            resumes = await supabase_service.get_user_resumes(candidate_id)
            skill_match_score = 0

            if resumes:
                resume = resumes[0]
                candidate_skills = resume.get("skills", [])
                match_result = calculate_skill_match_score(
                    candidate_skills=candidate_skills,
                    required_skills=required_skills
                )
                skill_match_score = match_result.get("match_score", 0)

            # Calculate combined score
            combined_score = (
                (interview_score * interview_weight) +
                (skill_match_score * skill_weight)
            )

            # Get profile
            profile = await supabase_service.get_profile(candidate_id)

            candidate_data = {
                "candidate_id": candidate_id,
                "candidate_name": profile.get("full_name") if profile else "Unknown",
                "candidate_avatar": profile.get("avatar_url") if profile else None,
                "interview_score": interview_score,
                "skill_match_score": skill_match_score,
                "combined_score": round(combined_score, 2),
                "interview_weight": interview_weight,
                "skill_weight": skill_weight
            }

            if candidate_interview and candidate_interview.get("interview_scores"):
                scores = candidate_interview["interview_scores"][0]
                candidate_data["technical_score"] = scores.get("technical_score")
                candidate_data["communication_score"] = scores.get("communication_score")
                candidate_data["recommendation"] = scores.get("recommendation")
                candidate_data["completed_at"] = candidate_interview.get("completed_at")

            if resumes:
                resume = resumes[0]
                match_result = calculate_skill_match_score(
                    candidate_skills=resume.get("skills", []),
                    required_skills=required_skills
                )
                candidate_data["matched_skills"] = match_result.get("matched_skills", [])
                candidate_data["missing_skills"] = match_result.get("missing_skills", [])

            combined_candidates.append(candidate_data)

        # Sort by combined score
        combined_candidates.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

        # Add ranks
        ranked_candidates = []
        for i, c in enumerate(combined_candidates):
            c["rank"] = i + 1
            ranked_candidates.append(c)

        return {
            "job_id": job_id,
            "job_title": job.get("title"),
            "ranking_weights": {
                "interview": interview_weight,
                "skill_match": skill_weight
            },
            "total_candidates": len(ranked_candidates),
            "candidates": ranked_candidates[:limit]
        }

    async def get_candidate_rankings_across_jobs(
        self,
        candidate_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a candidate's rankings across all jobs they've interviewed for.

        Args:
            candidate_id: Candidate user ID
            limit: Maximum number of jobs to return

        Returns:
            List of rankings per job
        """
        # Get completed interviews for candidate
        interviews = await self.supabase.table("interviews").select(
            "*, jobs(*), interview_scores(*)"
        ).eq("candidate_id", candidate_id).eq("status", "completed").execute()

        rankings = []

        for interview in interviews.data:
            job = interview.get("jobs")
            job_id = interview.get("job_id")

            if not job_id or not job:
                continue

            scores = interview.get("interview_scores", [{}])[0] if interview.get("interview_scores") else {}

            # Get rank for this job
            job_interviews = await self.supabase.table("interviews").select(
                "id"
            ).eq("job_id", job_id).eq("status", "completed").execute()

            # Count how many have higher scores
            higher_scores = 0
            for ji in job_interviews.data:
                if ji["id"] == interview.get("id"):
                    continue

                other_score = await self.supabase.table("interview_scores").select(
                    "overall_score"
                ).eq("interview_id", ji["id"]).execute()

                if other_score.data and other_score.data[0].get("overall_score"):
                    if other_score.data[0]["overall_score"] > scores.get("overall_score", 0):
                        higher_scores += 1

            rank = higher_scores + 1
            total = len(job_interviews.data)

            rankings.append({
                "job_id": job_id,
                "job_title": job.get("title") if job else None,
                "company": job.get("companies") if job and isinstance(job.get("companies"), dict) else None,
                "rank": rank,
                "total_candidates": total,
                "score": scores.get("overall_score"),
                "recommendation": scores.get("recommendation"),
                "completed_at": interview.get("completed_at")
            })

        # Sort by rank
        rankings.sort(key=lambda x: x.get("rank", 999))

        return rankings[:limit]

    async def compare_candidates(
        self,
        job_id: str,
        candidate_ids: List[str],
        recruiter_id: str
    ) -> Dict[str, Any]:
        """Compare multiple candidates for a job.

        Args:
            job_id: Job ID
            candidate_ids: List of candidate IDs to compare
            recruiter_id: Recruiter user ID (for authorization)

        Returns:
            Comparison data
        """
        # Verify access
        await self._verify_job_access(job_id, recruiter_id)

        # Get job details
        job = await supabase_service.get_job(job_id)

        # Get interviews for these candidates
        interviews = await self.supabase.table("interviews").select(
            "*, profiles!interviews_candidate_id_fkey(*), interview_scores(*)"
        ).eq("job_id", job_id).in_("candidate_id", candidate_ids).eq(
            "status", "completed"
        ).execute()

        # Build comparison
        comparisons = []

        for interview in interviews.data:
            profile = interview.get("profiles")
            scores = interview.get("interview_scores", [{}])[0] if interview.get("interview_scores") else {}

            # Get candidate skills
            resumes = await supabase_service.get_user_resumes(interview.get("candidate_id"))
            candidate_skills = resumes[0].get("skills", []) if resumes else []

            skill_match = calculate_skill_match_score(
                candidate_skills=candidate_skills,
                required_skills=job.get("skills_required", []) if job else []
            )

            comparisons.append({
                "candidate_id": interview.get("candidate_id"),
                "candidate_name": profile.get("full_name") if profile else "Unknown",
                "candidate_avatar": profile.get("avatar_url") if profile else None,
                "interview_score": scores.get("overall_score"),
                "technical_score": scores.get("technical_score"),
                "communication_score": scores.get("communication_score"),
                "problem_solving_score": scores.get("problem_solving_score"),
                "cultural_fit_score": scores.get("cultural_fit_score"),
                "skill_match_score": skill_match.get("match_score"),
                "matched_skills": skill_match.get("matched_skills", []),
                "missing_skills": skill_match.get("missing_skills", []),
                "recommendation": scores.get("recommendation"),
                "strengths": scores.get("strengths", []),
                "weaknesses": scores.get("weaknesses", [])
            })

        # Sort by overall score
        comparisons.sort(key=lambda x: x.get("interview_score", 0), reverse=True)

        # Calculate averages
        if comparisons:
            avg_interview = sum(c.get("interview_score", 0) or 0 for c in comparisons) / len(comparisons)
            avg_skill = sum(c.get("skill_match_score", 0) or 0 for c in comparisons) / len(comparisons)
        else:
            avg_interview = 0
            avg_skill = 0

        return {
            "job_id": job_id,
            "job_title": job.get("title") if job else None,
            "total_candidates": len(comparisons),
            "averages": {
                "interview_score": round(avg_interview, 1),
                "skill_match_score": round(avg_skill, 1)
            },
            "candidates": comparisons
        }

    async def _verify_job_access(
        self,
        job_id: str,
        recruiter_id: str
    ) -> None:
        """Verify that recruiter has access to the job.

        Args:
            job_id: Job ID
            recruiter_id: Recruiter user ID

        Raises:
            ValueError: If access denied
        """
        job = await supabase_service.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        companies = await supabase_service.list_companies(recruiter_id)
        company_ids = [c["id"] for c in companies]

        if job.get("company_id") not in company_ids:
            raise ValueError("Access denied to this job")


def create_ranking_service(supabase_client: AsyncClient) -> RankingService:
    """Create a RankingService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured RankingService instance
    """
    return RankingService(supabase_client)
