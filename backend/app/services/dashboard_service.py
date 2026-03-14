"""Dashboard Service for retrieving dashboard data for candidates and recruiters."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from supabase import AsyncClient

from app.services.supabase import supabase_service
from app.services.matching import matching_service


class DashboardService:
    """Service for retrieving dashboard data."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client
        """
        self.supabase = supabase_client

    async def get_candidate_dashboard(
        self,
        candidate_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get candidate dashboard data.

        Args:
            candidate_id: Candidate user ID
            limit: Maximum number of items to return

        Returns:
            Candidate dashboard data including recommended jobs, interviews, etc.
        """
        # Get recommended jobs
        recommended_jobs = await matching_service.find_matching_jobs(
            candidate_id=candidate_id,
            limit=limit,
            use_ai=False  # Use faster matching for dashboard
        )

        # Get available interviews (scheduled and in_progress)
        available_interviews = await self.supabase.table("interviews").select(
            "*, jobs(*)"
        ).eq("candidate_id", candidate_id).in_(
            "status", ["scheduled", "ready"]
        ).order("created_at", desc=True).limit(limit).execute()

        # Get interview history (completed interviews)
        interview_history = await self._get_candidate_interview_history(
            candidate_id, limit
        )

        # Calculate statistics
        total_interviews = len(interview_history)
        average_score = None

        if total_interviews > 0:
            scores = [
                h.get("interview_scores", [{}])[0].get("overall_score")
                for h in interview_history
                if h.get("interview_scores") and h["interview_scores"][0].get("overall_score")
            ]
            if scores:
                average_score = round(sum(scores) / len(scores), 1)

        return {
            "recommended_jobs": recommended_jobs[:limit],
            "available_interviews": available_interviews.data,
            "interview_history": interview_history,
            "average_score": average_score,
            "total_interviews": total_interviews
        }

    async def get_recruiter_dashboard(
        self,
        recruiter_id: str,
        company_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get recruiter dashboard data.

        Args:
            recruiter_id: Recruiter user ID
            company_id: Company ID to filter by
            limit: Maximum number of items to return

        Returns:
            Recruiter dashboard data including company, jobs, candidates, etc.
        """
        # Get company (or first company owned by recruiter)
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
                "active_jobs": [],
                "total_candidates": 0,
                "recent_interviews": [],
                "top_candidates": []
            }

        company_id = company["id"]

        # Get active jobs for company
        active_jobs = await self.supabase.table("jobs").select("*").eq(
            "company_id", company_id
        ).eq("is_active", True).order("created_at", desc=True).limit(limit).execute()

        # Get all candidates who have interviews for company's jobs
        job_ids = [job["id"] for job in active_jobs.data]
        total_candidates = 0

        if job_ids:
            # Count unique candidates with interviews for these jobs
            candidates_result = await self.supabase.table("interviews").select(
                "candidate_id", count="exact"
            ).in_("job_id", job_ids).execute()
            total_candidates = candidates_result.count or 0

        # Get recent interviews
        recent_interviews = await self.supabase.table("interviews").select(
            "*, jobs(*), profiles!interviews_candidate_id_fkey(full_name)"
        ).in_("job_id", job_ids).order(
            "created_at", desc=True
        ).limit(limit).execute() if job_ids else []

        # Get top candidates (highest scores across all interviews)
        top_candidates = await self._get_top_candidates_for_company(
            company_id, limit
        )

        return {
            "company": company,
            "active_jobs": active_jobs.data,
            "total_candidates": total_candidates,
            "recent_interviews": recent_interviews.data,
            "top_candidates": top_candidates
        }

    async def _get_candidate_interview_history(
        self,
        candidate_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get completed interview history for a candidate.

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

        return interviews.data

    async def _get_top_candidates_for_company(
        self,
        company_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top performing candidates for a company.

        Args:
            company_id: Company ID
            limit: Maximum number to return

        Returns:
            List of top candidates with scores
        """
        # Get jobs for company
        jobs = await self.supabase.table("jobs").select("id").eq(
            "company_id", company_id
        ).execute()

        if not jobs.data:
            return []

        job_ids = [j["id"] for j in jobs.data]

        # Get completed interviews with scores for these jobs
        interviews = await self.supabase.table("interviews").select(
            "*, interview_scores(*), profiles!interviews_candidate_id_fkey(*)"
        ).in_("job_id", job_ids).eq("status", "completed").execute()

        # Calculate average score per candidate
        candidate_scores: Dict[str, Dict] = {}

        for interview in interviews.data:
            if not interview.get("interview_scores"):
                continue

            score = interview["interview_scores"][0].get("overall_score", 0)
            if not score:
                continue

            candidate_id = interview.get("candidate_id")
            if candidate_id:
                if candidate_id not in candidate_scores:
                    profile = interview.get("profiles")
                    candidate_scores[candidate_id] = {
                        "candidate_id": candidate_id,
                        "candidate_name": profile.get("full_name") if profile else "Unknown",
                        "total_score": 0,
                        "interview_count": 0,
                        "average_score": 0
                    }

                candidate_scores[candidate_id]["total_score"] += score
                candidate_scores[candidate_id]["interview_count"] += 1

        # Calculate averages and sort
        top_candidates = []
        for candidate_id, data in candidate_scores.items():
            if data["interview_count"] > 0:
                data["average_score"] = round(
                    data["total_score"] / data["interview_count"], 1
                )
                top_candidates.append(data)

        # Sort by average score descending
        top_candidates.sort(key=lambda x: x["average_score"], reverse=True)

        return top_candidates[:limit]

    async def get_interview_statistics(
        self,
        user_id: str,
        user_type: str = "candidate"
    ) -> Dict[str, Any]:
        """Get interview statistics for a user.

        Args:
            user_id: User ID
            user_type: Either "candidate" or "recruiter"

        Returns:
            Statistics data
        """
        if user_type == "candidate":
            return await self._get_candidate_statistics(user_id)
        else:
            return await self._get_recruiter_statistics(user_id)

    async def _get_candidate_statistics(
        self,
        candidate_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a candidate.

        Args:
            candidate_id: Candidate user ID

        Returns:
            Candidate statistics
        """
        # Get all interviews
        interviews = await self.supabase.table("interviews").select(
            "*, interview_scores(*)"
        ).eq("candidate_id", candidate_id).execute()

        total = len(interviews.data)
        completed = len([i for i in interviews.data if i.get("status") == "completed"])
        scheduled = len([i for i in interviews.data if i.get("status") in ["scheduled", "ready"]])
        in_progress = len([i for i in interviews.data if i.get("status") == "in_progress"])

        # Calculate average score
        scores = [
            i["interview_scores"][0].get("overall_score")
            for i in interviews.data
            if i.get("interview_scores") and i["interview_scores"][0].get("overall_score")
        ]

        average_score = round(sum(scores) / len(scores), 1) if scores else None

        # Get recommendations breakdown
        recommendations = {}
        for interview in interviews.data:
            if interview.get("interview_scores"):
                rec = interview["interview_scores"][0].get("recommendation", "unknown")
                recommendations[rec] = recommendations.get(rec, 0) + 1

        return {
            "total_interviews": total,
            "completed_interviews": completed,
            "scheduled_interviews": scheduled,
            "in_progress_interviews": in_progress,
            "average_score": average_score,
            "total_scores": len(scores),
            "recommendations": recommendations
        }

    async def _get_recruiter_statistics(
        self,
        recruiter_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a recruiter.

        Args:
            recruiter_id: Recruiter user ID

        Returns:
            Recruiter statistics
        """
        # Get companies owned by recruiter
        companies = await supabase_service.list_companies(recruiter_id)

        if not companies:
            return {
                "total_jobs": 0,
                "total_interviews": 0,
                "total_candidates": 0,
                "average_candidate_score": None
            }

        company_ids = [c["id"] for c in companies]

        # Get jobs
        jobs = await self.supabase.table("jobs").select("id").in_(
            "company_id", company_ids
        ).execute()

        job_ids = [j["id"] for j in jobs.data]
        total_jobs = len(jobs.data)

        # Get interviews
        interviews = []
        if job_ids:
            interviews = await self.supabase.table("interviews").select(
                "*, interview_scores(*)"
            ).in_("job_id", job_ids).execute()

        total_interviews = len(interviews.data)
        completed = len([i for i in interviews.data if i.get("status") == "completed"])

        # Count unique candidates
        candidate_ids = set(
            i.get("candidate_id") for i in interviews.data if i.get("candidate_id")
        )
        total_candidates = len(candidate_ids)

        # Calculate average candidate score
        scores = [
            i["interview_scores"][0].get("overall_score")
            for i in interviews.data
            if i.get("interview_scores") and i["interview_scores"][0].get("overall_score")
        ]

        average_score = round(sum(scores) / len(scores), 1) if scores else None

        return {
            "total_jobs": total_jobs,
            "total_interviews": total_interviews,
            "completed_interviews": completed,
            "total_candidates": total_candidates,
            "average_candidate_score": average_score,
            "total_scores": len(scores)
        }


def create_dashboard_service(supabase_client: AsyncClient) -> DashboardService:
    """Create a DashboardService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured DashboardService instance
    """
    return DashboardService(supabase_client)
