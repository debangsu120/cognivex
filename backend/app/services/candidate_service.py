"""Candidate Service for managing candidate-specific operations."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from supabase import AsyncClient

from app.services.supabase import supabase_service
from app.services.matching import matching_service


class CandidateService:
    """Service for candidate-specific operations."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client
        """
        self.supabase = supabase_client

    async def get_candidate_profile(
        self,
        candidate_id: str,
        include_resume: bool = True
    ) -> Dict[str, Any]:
        """Get candidate profile with skills and resume.

        Args:
            candidate_id: Candidate user ID
            include_resume: Whether to include resume data

        Returns:
            Candidate profile data
        """
        # Get user profile
        profile = await supabase_service.get_profile(candidate_id)

        # Get resume(s)
        resumes = []
        skills = []

        if include_resume:
            resumes = await supabase_service.get_user_resumes(candidate_id)
            if resumes:
                # Extract skills from resume
                skills = resumes[0].get("skills", [])

        # Get completed interview count
        interviews = await self.supabase.table("interviews").select(
            "id", count="exact"
        ).eq("candidate_id", candidate_id).eq("status", "completed").execute()

        completed_count = interviews.count or 0

        # Get average score
        scores_data = await self.supabase.table("interview_scores").select(
            "overall_score"
        ).execute()

        # Get scores for this candidate's interviews
        candidate_interviews = await self.supabase.table("interviews").select(
            "id"
        ).eq("candidate_id", candidate_id).execute()

        interview_ids = [i["id"] for i in candidate_interviews.data]

        if interview_ids:
            scores = await self.supabase.table("interview_scores").select(
                "overall_score"
            ).in_("interview_id", interview_ids).execute()

            score_values = [
                s["overall_score"] for s in scores.data if s.get("overall_score")
            ]
            average_score = round(sum(score_values) / len(score_values), 1) if score_values else None
        else:
            average_score = None

        return {
            "candidate_id": candidate_id,
            "profile": profile,
            "resumes": resumes,
            "skills": skills,
            "completed_interviews": completed_count,
            "average_score": average_score
        }

    async def get_candidate_interview_history(
        self,
        candidate_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get interview history for a candidate.

        Args:
            candidate_id: Candidate user ID
            status: Filter by status (completed, scheduled, in_progress, etc.)
            limit: Maximum number to return
            offset: Offset for pagination

        Returns:
            List of interviews
        """
        query = self.supabase.table("interviews").select(
            "*, jobs(*), interview_scores(*)"
        ).eq("candidate_id", candidate_id)

        if status:
            query = query.eq("status", status)

        interviews = query.order(
            "created_at", desc=True
        ).range(offset, offset + limit - 1).execute()

        return interviews.data

    async def get_available_interviews(
        self,
        candidate_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get available interviews for a candidate.

        Args:
            candidate_id: Candidate user ID
            limit: Maximum number to return

        Returns:
            List of available (scheduled/ready) interviews
        """
        interviews = await self.supabase.table("interviews").select(
            "*, jobs(*)"
        ).eq("candidate_id", candidate_id).in_(
            "status", ["scheduled", "ready"]
        ).order("created_at", desc=True).limit(limit).execute()

        return interviews.data

    async def get_past_results(
        self,
        candidate_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get past interview results for a candidate.

        Args:
            candidate_id: Candidate user ID
            limit: Maximum number to return

        Returns:
            List of completed interviews with scores
        """
        interviews = await self.supabase.table("interviews").select(
            "*, jobs(*), interview_scores(*)"
        ).eq("candidate_id", candidate_id).eq(
            "status", "completed"
        ).order("completed_at", desc=True).limit(limit).execute()

        # Enrich with job company info
        results = []
        for interview in interviews.data:
            job = interview.get("jobs", {})
            company = job.get("companies", {}) if isinstance(job, dict) else {}

            results.append({
                "interview_id": interview.get("id"),
                "job_title": job.get("title") if job else None,
                "company_name": company.get("name") if company else None,
                "status": interview.get("status"),
                "completed_at": interview.get("completed_at"),
                "difficulty": interview.get("difficulty"),
                "scores": interview.get("interview_scores", [{}])[0] if interview.get("interview_scores") else None
            })

        return results

    async def get_candidate_applications(
        self,
        candidate_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get job applications for a candidate.

        Args:
            candidate_id: Candidate user ID
            limit: Maximum number to return

        Returns:
            List of job applications
        """
        # This would typically query an applications table
        # For now, return interviews as applications
        interviews = await self.supabase.table("interviews").select(
            "*, jobs(*)"
        ).eq("candidate_id", candidate_id).order(
            "created_at", desc=True
        ).limit(limit).execute()

        applications = []
        for interview in interviews.data:
            job = interview.get("jobs", {})
            applications.append({
                "interview_id": interview.get("id"),
                "job_id": interview.get("job_id"),
                "job_title": job.get("title") if job else None,
                "company_id": job.get("company_id") if job else None,
                "status": interview.get("status"),
                "applied_at": interview.get("created_at"),
                "interview_status": interview.get("status")
            })

        return applications

    async def get_candidate_skill_profile(
        self,
        candidate_id: str
    ) -> Dict[str, Any]:
        """Get detailed skill profile for a candidate.

        Args:
            candidate_id: Candidate user ID

        Returns:
            Skill profile data
        """
        # Get resumes
        resumes = await supabase_service.get_user_resumes(candidate_id)

        all_skills = []
        for resume in resumes:
            skills = resume.get("skills", [])
            all_skills.extend(skills)

        # Remove duplicates
        unique_skills = list(set(all_skills))

        # Get skill categories from interviews
        skill_categories: Dict[str, List[str]] = {}

        # Get completed interviews
        interviews = await self.supabase.table("interviews").select(
            "id"
        ).eq("candidate_id", candidate_id).eq("status", "completed").execute()

        interview_ids = [i["id"] for i in interviews.data]

        if interview_ids:
            # Get questions with skills
            questions = await self.supabase.table("interview_questions").select(
                "skill, category"
            ).in_("interview_id", interview_ids).execute()

            for q in questions.data:
                skill = q.get("skill")
                category = q.get("category", "general")

                if skill:
                    if category not in skill_categories:
                        skill_categories[category] = []
                        if skill not in skill_categories[category]:
                            skill_categories[category].append(skill)

        return {
            "candidate_id": candidate_id,
            "skills": unique_skills,
            "skills_by_category": skill_categories,
            "total_skills": len(unique_skills),
            "resumes_count": len(resumes)
        }

    async def get_candidate_performance_trend(
        self,
        candidate_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get performance trend over time for a candidate.

        Args:
            candidate_id: Candidate user ID
            limit: Number of recent interviews to analyze

        Returns:
            Performance trend data
        """
        interviews = await self.supabase.table("interviews").select(
            "*, interview_scores(*)"
        ).eq("candidate_id", candidate_id).eq(
            "status", "completed"
        ).order("completed_at", asc=True).limit(limit).execute()

        trend = []
        running_average = []

        total_score = 0
        count = 0

        for interview in interviews.data:
            score_data = interview.get("interview_scores", [{}])[0]

            if score_data.get("overall_score"):
                total_score += score_data["overall_score"]
                count += 1
                running_average.append(round(total_score / count, 1))

                trend.append({
                    "interview_id": interview.get("id"),
                    "completed_at": interview.get("completed_at"),
                    "overall_score": score_data.get("overall_score"),
                    "technical_score": score_data.get("technical_score"),
                    "communication_score": score_data.get("communication_score"),
                    "problem_solving_score": score_data.get("problem_solving_score"),
                    "cultural_fit_score": score_data.get("cultural_fit_score"),
                    "running_average": running_average[-1],
                    "recommendation": score_data.get("recommendation")
                })

        return trend


def create_candidate_service(supabase_client: AsyncClient) -> CandidateService:
    """Create a CandidateService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured CandidateService instance
    """
    return CandidateService(supabase_client)
