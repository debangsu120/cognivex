"""Recruiter Service for managing recruiter-specific operations."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from supabase import AsyncClient

from app.services.supabase import supabase_service


class RecruiterService:
    """Service for recruiter-specific operations."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client
        """
        self.supabase = supabase_client

    async def get_company_dashboard(
        self,
        recruiter_id: str,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get company dashboard data for a recruiter.

        Args:
            recruiter_id: Recruiter user ID
            company_id: Company ID (if None, gets first company)

        Returns:
            Company dashboard data
        """
        # Get company
        if company_id:
            company = await supabase_service.get_company(company_id)
            if not company or company.get("owner_id") != recruiter_id:
                raise ValueError("Company not found or access denied")
        else:
            companies = await supabase_service.list_companies(recruiter_id)
            company = companies[0] if companies else None

        if not company:
            return {
                "company": None,
                "stats": {
                    "total_jobs": 0,
                    "active_jobs": 0,
                    "total_candidates": 0,
                    "total_interviews": 0,
                    "completed_interviews": 0
                },
                "recent_activity": []
            }

        company_id = company["id"]

        # Get job stats
        all_jobs = await self.supabase.table("jobs").select(
            "id", count="exact"
        ).eq("company_id", company_id).execute()

        active_jobs = await self.supabase.table("jobs").select(
            "id", count="exact"
        ).eq("company_id", company_id).eq("is_active", True).execute()

        job_ids_result = await self.supabase.table("jobs").select("id").eq(
            "company_id", company_id
        ).execute()
        job_ids = [j["id"] for j in job_ids_result.data]

        # Get candidate/interview stats
        total_candidates = 0
        total_interviews = 0
        completed_interviews = 0

        if job_ids:
            # Get unique candidates
            candidates_result = await self.supabase.table("interviews").select(
                "candidate_id", count="exact"
            ).in_("job_id", job_ids).execute()
            total_candidates = candidates_result.count or 0

            # Get interview counts
            interviews_result = await self.supabase.table("interviews").select(
                "id", count="exact"
            ).in_("job_id", job_ids).execute()
            total_interviews = interviews_result.count or 0

            completed_result = await self.supabase.table("interviews").select(
                "id", count="exact"
            ).in_("job_id", job_ids).eq("status", "completed").execute()
            completed_interviews = completed_result.count or 0

        # Get recent activity
        recent_activity = await self._get_recent_activity(job_ids)

        return {
            "company": company,
            "stats": {
                "total_jobs": all_jobs.count or 0,
                "active_jobs": active_jobs.count or 0,
                "total_candidates": total_candidates,
                "total_interviews": total_interviews,
                "completed_interviews": completed_interviews
            },
            "recent_activity": recent_activity
        }

    async def get_candidates_for_job(
        self,
        job_id: str,
        recruiter_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get candidates for a specific job.

        Args:
            job_id: Job ID
            recruiter_id: Recruiter user ID (for authorization)
            status: Filter by interview status
            limit: Maximum number to return
            offset: Offset for pagination

        Returns:
            List of candidates with interview data
        """
        # Verify job belongs to recruiter's company
        job = await supabase_service.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        companies = await supabase_service.list_companies(recruiter_id)
        company_ids = [c["id"] for c in companies]

        if job.get("company_id") not in company_ids:
            raise ValueError("Access denied to this job")

        # Get interviews for this job
        query = self.supabase.table("interviews").select(
            "*, profiles!interviews_candidate_id_fkey(*), interview_scores(*)"
        ).eq("job_id", job_id)

        if status:
            query = query.eq("status", status)

        interviews = query.order(
            "created_at", desc=True
        ).range(offset, offset + limit - 1).execute()

        # Format candidate data
        candidates = []
        for interview in interviews.data:
            profile = interview.get("profiles")
            score = interview.get("interview_scores", [{}])[0] if interview.get("interview_scores") else {}

            candidates.append({
                "interview_id": interview.get("id"),
                "candidate_id": interview.get("candidate_id"),
                "candidate_name": profile.get("full_name") if profile else None,
                "candidate_email": profile.get("email") if profile else None,
                "candidate_avatar": profile.get("avatar_url") if profile else None,
                "status": interview.get("status"),
                "created_at": interview.get("created_at"),
                "completed_at": interview.get("completed_at"),
                "score": score.get("overall_score") if score else None,
                "technical_score": score.get("technical_score") if score else None,
                "communication_score": score.get("communication_score") if score else None,
                "recommendation": score.get("recommendation") if score else None
            })

        return candidates

    async def get_job_ranking(
        self,
        job_id: str,
        recruiter_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get ranked candidates for a job.

        Args:
            job_id: Job ID
            recruiter_id: Recruiter user ID (for authorization)
            limit: Maximum number to return

        Returns:
            Ranked list of candidates
        """
        # Verify job belongs to recruiter's company
        job = await supabase_service.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        companies = await supabase_service.list_companies(recruiter_id)
        company_ids = [c["id"] for c in companies]

        if job.get("company_id") not in company_ids:
            raise ValueError("Access denied to this job")

        # Get completed interviews with scores
        interviews = await self.supabase.table("interviews").select(
            "*, profiles!interviews_candidate_id_fkey(*), interview_scores(*)"
        ).eq("job_id", job_id).eq("status", "completed").execute()

        # Rank by overall score
        ranked_candidates = []
        for interview in interviews.data:
            profile = interview.get("profiles")
            score = interview.get("interview_scores", [{}])[0] if interview.get("interview_scores") else {}

            if score.get("overall_score"):
                ranked_candidates.append({
                    "interview_id": interview.get("id"),
                    "candidate_id": interview.get("candidate_id"),
                    "candidate_name": profile.get("full_name") if profile else None,
                    "candidate_avatar": profile.get("avatar_url") if profile else None,
                    "overall_score": score.get("overall_score"),
                    "technical_score": score.get("technical_score"),
                    "communication_score": score.get("communication_score"),
                    "problem_solving_score": score.get("problem_solving_score"),
                    "cultural_fit_score": score.get("cultural_fit_score"),
                    "recommendation": score.get("recommendation"),
                    "completed_at": interview.get("completed_at"),
                    "strengths": score.get("strengths", []),
                    "weaknesses": score.get("weaknesses", [])
                })

        # Sort by score descending
        ranked_candidates.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        # Add rank
        for i, candidate in enumerate(ranked_candidates):
            candidate["rank"] = i + 1

        return ranked_candidates[:limit]

    async def get_all_jobs_with_candidates(
        self,
        recruiter_id: str,
        company_id: Optional[str] = None,
        include_stats: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all jobs with candidate counts and stats.

        Args:
            recruiter_id: Recruiter user ID
            company_id: Company ID (if None, gets all companies)
            include_stats: Whether to include candidate stats

        Returns:
            List of jobs with candidate information
        """
        # Get companies
        if company_id:
            companies = [await supabase_service.get_company(company_id)]
        else:
            companies = await supabase_service.list_companies(recruiter_id)

        if not companies:
            return []

        company_ids = [c["id"] for c in companies if c]

        # Get all jobs
        jobs = await self.supabase.table("jobs").select(
            "*, companies(*)"
        ).in_("company_id", company_ids).order("created_at", desc=True).execute()

        jobs_data = []

        for job in jobs.data:
            job_id = job["id"]

            job_info = {
                "job_id": job_id,
                "title": job.get("title"),
                "company": job.get("companies"),
                "status": "active" if job.get("is_active") else "inactive",
                "created_at": job.get("created_at"),
                "location": job.get("location"),
                "job_type": job.get("job_type")
            }

            if include_stats:
                # Get candidate stats
                interviews = await self.supabase.table("interviews").select(
                    "id, status", count="exact"
                ).eq("job_id", job_id).execute()

                candidates_result = await self.supabase.table("interviews").select(
                    "candidate_id", count="exact"
                ).eq("job_id", job_id).execute()

                completed_result = await self.supabase.table("interviews").select(
                    "id", count="exact"
                ).eq("job_id", job_id).eq("status", "completed").execute()

                # Calculate average score
                interview_ids_result = await self.supabase.table("interviews").select(
                    "id"
                ).eq("job_id", job_id).execute()
                interview_ids = [i["id"] for i in interview_ids_result.data]

                avg_score = None
                if interview_ids:
                    scores = await self.supabase.table("interview_scores").select(
                        "overall_score"
                    ).in_("interview_id", interview_ids).execute()

                    score_values = [
                        s["overall_score"] for s in scores.data if s.get("overall_score")
                    ]
                    if score_values:
                        avg_score = round(sum(score_values) / len(score_values), 1)

                job_info["stats"] = {
                    "total_interviews": interviews.count or 0,
                    "unique_candidates": candidates_result.count or 0,
                    "completed_interviews": completed_result.count or 0,
                    "average_score": avg_score
                }

            jobs_data.append(job_info)

        return jobs_data

    async def manage_job_posting(
        self,
        job_id: str,
        recruiter_id: str,
        action: str,
        job_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Manage job posting (activate, deactivate, update).

        Args:
            job_id: Job ID
            recruiter_id: Recruiter user ID
            action: Action to perform (activate, deactivate, update)
            job_data: Data for update action

        Returns:
            Updated job data
        """
        # Verify job belongs to recruiter's company
        job = await supabase_service.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        companies = await supabase_service.list_companies(recruiter_id)
        company_ids = [c["id"] for c in companies]

        if job.get("company_id") not in company_ids:
            raise ValueError("Access denied to this job")

        if action == "activate":
            updated = await supabase_service.update_job(job_id, {"is_active": True})
            return {"job": updated, "action": "activated"}

        elif action == "deactivate":
            updated = await supabase_service.update_job(job_id, {"is_active": False})
            return {"job": updated, "action": "deactivated"}

        elif action == "update":
            if not job_data:
                raise ValueError("Job data required for update action")
            updated = await supabase_service.update_job(job_id, job_data)
            return {"job": updated, "action": "updated"}

        else:
            raise ValueError(f"Invalid action: {action}")

    async def get_recruiter_candidates_summary(
        self,
        recruiter_id: str,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of all candidates across recruiter's jobs.

        Args:
            recruiter_id: Recruiter user ID
            company_id: Company ID (if None, gets all)

        Returns:
            Summary data
        """
        # Get companies
        if company_id:
            companies = [await supabase_service.get_company(company_id)]
        else:
            companies = await supabase_service.list_companies(recruiter_id)

        if not companies:
            return {"total_candidates": 0, "candidates_by_status": {}}

        company_ids = [c["id"] for c in companies if c]

        # Get jobs
        jobs_result = await self.supabase.table("jobs").select("id").in_(
            "company_id", company_ids
        ).execute()
        job_ids = [j["id"] for j in jobs_result.data]

        if not job_ids:
            return {
                "total_candidates": 0,
                "candidates_by_status": {},
                "top_skills": []
            }

        # Get candidates grouped by status
        status_counts = {}
        for status in ["scheduled", "ready", "in_progress", "completed", "cancelled"]:
            count_result = await self.supabase.table("interviews").select(
                "id", count="exact"
            ).in_("job_id", job_ids).eq("status", status).execute()
            status_counts[status] = count_result.count or 0

        # Get unique candidates
        candidates_result = await self.supabase.table("interviews").select(
            "candidate_id"
        ).in_("job_id", job_ids).execute()

        unique_candidate_ids = list(set(
            c["candidate_id"] for c in candidates_result.data if c.get("candidate_id")
        ))

        return {
            "total_candidates": len(unique_candidate_ids),
            "candidates_by_status": status_counts,
            "total_interviews": sum(status_counts.values())
        }

    async def _get_recent_activity(
        self,
        job_ids: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activity across jobs.

        Args:
            job_ids: List of job IDs
            limit: Maximum items to return

        Returns:
            Recent activity list
        """
        if not job_ids:
            return []

        interviews = await self.supabase.table("interviews").select(
            "*, jobs(*), profiles!interviews_candidate_id_fkey(*)"
        ).in_("job_id", job_ids).order("updated_at", desc=True).limit(limit).execute()

        activities = []
        for interview in interviews.data:
            profile = interview.get("profiles")
            job = interview.get("jobs")

            status = interview.get("status")
            activity_type = "interview_updated"

            if status == "completed":
                activity_type = "interview_completed"
            elif status in ["scheduled", "ready"]:
                activity_type = "interview_scheduled"

            activities.append({
                "type": activity_type,
                "interview_id": interview.get("id"),
                "candidate_name": profile.get("full_name") if profile else "Unknown",
                "job_title": job.get("title") if job else None,
                "status": status,
                "timestamp": interview.get("updated_at") or interview.get("created_at")
            })

        return activities


def create_recruiter_service(supabase_client: AsyncClient) -> RecruiterService:
    """Create a RecruiterService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured RecruiterService instance
    """
    return RecruiterService(supabase_client)
