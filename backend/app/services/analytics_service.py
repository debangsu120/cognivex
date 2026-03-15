"""
Analytics Service for Hiring Intelligence

Provides analytics and insights for recruiters including:
- Skill gap analysis
- Candidate performance metrics
- Hiring trends
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from supabase import AsyncClient

from app.services.supabase import supabase_service


class AnalyticsService:
    """Service for hiring intelligence analytics."""

    def __init__(self, supabase_client: AsyncClient):
        self.supabase = supabase_client

    async def get_skill_gap_analysis(
        self,
        job_id: str,
        recruiter_id: str
    ) -> Dict[str, Any]:
        """Analyze skill gaps for a job based on candidate performance.

        Args:
            job_id: Job ID to analyze
            recruiter_id: Recruiter requesting the analysis

        Returns:
            Skill gap analysis with recommendations
        """
        # Verify access
        job = await supabase_service.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        required_skills = job.get("skills_required", [])

        if not required_skills:
            return {
                "job_id": job_id,
                "job_title": job.get("title"),
                "required_skills": [],
                "skill_gaps": [],
                "message": "No required skills defined for this job"
            }

        # Get completed interviews for this job
        interviews = await self.supabase.table("interviews").select(
            "id"
        ).eq("job_id", job_id).eq("status", "completed").execute()

        interview_ids = [i["id"] for i in interviews.data]

        if not interview_ids:
            return {
                "job_id": job_id,
                "job_title": job.get("title"),
                "required_skills": required_skills,
                "skill_gaps": [],
                "candidates_analyzed": 0,
                "message": "No completed interviews yet"
            }

        # Get all questions and answers
        questions = await self.supabase.table("interview_questions").select(
            "id, skill, question_text"
        ).in_("interview_id", interview_ids).execute()

        # Group by skill
        skill_scores: Dict[str, List[float]] = {}
        for q in questions.data:
            skill = q.get("skill") or "general"
            if skill not in skill_scores:
                skill_scores[skill] = []

            # Get scores for this question across all interviews
            answers = await self.supabase.table("interview_answers").select(
                "score"
            ).eq("question_id", q["id"]).execute()

            for a in answers.data:
                if a.get("score") is not None:
                    skill_scores[skill].append(a["score"])

        # Calculate gaps
        skill_gaps = []
        for skill in required_skills:
            scores = skill_scores.get(skill, [])
            avg_score = sum(scores) / len(scores) if scores else None

            if avg_score is not None:
                gap = 10 - avg_score  # Assuming 10-point scale
                skill_gaps.append({
                    "skill": skill,
                    "average_score": round(avg_score, 1),
                    "gap_score": round(gap, 1),
                    "gap_level": "low" if gap < 2 else "medium" if gap < 4 else "high",
                    "candidates_tested": len(scores)
                })
            else:
                skill_gaps.append({
                    "skill": skill,
                    "average_score": None,
                    "gap_score": None,
                    "gap_level": "unknown",
                    "candidates_tested": 0,
                    "note": "No candidates tested on this skill yet"
                })

        # Sort by gap level
        gap_order = {"high": 0, "medium": 1, "low": 2, "unknown": 3}
        skill_gaps.sort(key=lambda x: gap_order.get(x["gap_level"], 3))

        return {
            "job_id": job_id,
            "job_title": job.get("title"),
            "required_skills": required_skills,
            "skill_gaps": skill_gaps,
            "candidates_analyzed": len(interview_ids),
            "overall_average": round(
                sum(s["average_score"] or 0 for s in skill_gaps) / len(skill_gaps)
                if skill_gaps else 0, 1
            )
        }

    async def get_candidate_trend_analysis(
        self,
        job_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze candidate performance trends over time.

        Args:
            job_id: Job ID to analyze
            days: Number of days to analyze

        Returns:
            Trend analysis with daily/weekly metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get completed interviews
        interviews = await self.supabase.table("interviews").select(
            "id, created_at, completed_at"
        ).eq("job_id", job_id).eq("status", "completed").gte(
            "completed_at", start_date.isoformat()
        ).execute()

        interview_ids = [i["id"] for i in interviews.data]

        if not interview_ids:
            return {
                "job_id": job_id,
                "period_days": days,
                "total_interviews": 0,
                "trends": [],
                "message": "No completed interviews in this period"
            }

        # Get scores
        scores = await self.supabase.table("interview_scores").select(
            "interview_id, overall_score, technical_score, communication_score"
        ).in_("interview_id", interview_ids).execute()

        # Group by day
        daily_scores: Dict[str, List[float]] = {}
        for score in scores.data:
            interview = next((i for i in interviews.data if i["id"] == score["interview_id"]), None)
            if interview and interview.get("completed_at"):
                day = interview["completed_at"][:10]  # YYYY-MM-DD
                if day not in daily_scores:
                    daily_scores[day] = []
                if score.get("overall_score"):
                    daily_scores[day].append(score["overall_score"])

        # Calculate daily averages
        trends = []
        for day, scores_list in sorted(daily_scores.items()):
            trends.append({
                "date": day,
                "interviews": len(scores_list),
                "average_score": round(sum(scores_list) / len(scores_list), 1),
                "min_score": min(scores_list),
                "max_score": max(scores_list)
            })

        # Calculate trend direction
        if len(trends) >= 2:
            first_half = trends[:len(trends)//2]
            second_half = trends[len(trends)//2:]

            first_avg = sum(t["average_score"] for t in first_half) / len(first_half)
            second_avg = sum(t["average_score"] for t in second_half) / len(second_half)

            if second_avg - first_avg > 3:
                trend_direction = "improving"
            elif first_avg - second_avg > 3:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"

        return {
            "job_id": job_id,
            "period_days": days,
            "total_interviews": len(interview_ids),
            "trends": trends,
            "trend_direction": trend_direction,
            "average_overall": round(
                sum(s.get("overall_score", 0) for s in scores.data
                    if s.get("overall_score")) / len(scores.data), 1
            ) if scores.data else None
        }

    async def get_overall_company_analytics(
        self,
        company_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get overall analytics for a company.

        Args:
            company_id: Company ID
            period_days: Number of days to analyze

        Returns:
            Company-wide analytics
        """
        start_date = datetime.utcnow() - timedelta(days=period_days)

        # Get jobs for company
        jobs = await self.supabase.table("jobs").select("id, title").eq(
            "company_id", company_id
        ).execute()

        job_ids = [j["id"] for j in jobs.data]

        if not job_ids:
            return {
                "company_id": company_id,
                "period_days": period_days,
                "total_jobs": 0,
                "message": "No jobs found for this company"
            }

        # Get interviews
        interviews = await self.supabase.table("interviews").select(
            "id, status, created_at"
        ).in_("job_id", job_ids).gte("created_at", start_date.isoformat()).execute()

        total_interviews = len(interviews.data)
        completed = sum(1 for i in interviews.data if i["status"] == "completed")

        # Get unique candidates
        candidate_ids = set()
        for i in interviews.data:
            # Would need to join with profiles - simplified for now
            pass

        # Get scores for completed
        completed_ids = [i["id"] for i in interviews.data if i["status"] == "completed"]
        if completed_ids:
            scores = await self.supabase.table("interview_scores").select(
                "overall_score, technical_score, communication_score"
            ).in_("interview_id", completed_ids).execute()

            score_values = [s["overall_score"] for s in scores.data if s.get("overall_score")]
            avg_score = sum(score_values) / len(score_values) if score_values else None

            technical = [s["technical_score"] for s in scores.data if s.get("technical_score")]
            avg_technical = sum(technical) / len(technical) if technical else None

            communication = [s["communication_score"] for s in scores.data if s.get("communication_score")]
            avg_communication = sum(communication) / len(communication) if communication else None
        else:
            avg_score = avg_technical = avg_communication = None

        return {
            "company_id": company_id,
            "period_days": period_days,
            "total_jobs": len(job_ids),
            "total_interviews": total_interviews,
            "completed_interviews": completed,
            "completion_rate": round(completed / total_interviews * 100, 1) if total_interviews > 0 else 0,
            "average_scores": {
                "overall": round(avg_score, 1) if avg_score else None,
                "technical": round(avg_technical, 1) if avg_technical else None,
                "communication": round(avg_communication, 1) if avg_communication else None
            }
        }

    async def get_top_performing_candidates(
        self,
        company_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top performing candidates across all jobs.

        Args:
            company_id: Company ID
            limit: Number of candidates to return

        Returns:
            List of top candidates with scores
        """
        # Get jobs for company
        jobs = await self.supabase.table("jobs").select("id").eq(
            "company_id", company_id
        ).execute()

        job_ids = [j["id"] for j in jobs.data]

        if not job_ids:
            return []

        # Get completed interviews with scores
        interviews = await self.supabase.table("interviews").select(
            "id, job_id, candidate_id"
        ).in_("job_id", job_ids).eq("status", "completed").execute()

        interview_ids = [i["id"] for i in interviews.data]

        if not interview_ids:
            return []

        # Get scores
        scores = await self.supabase.table("interview_scores").select(
            "interview_id, overall_score, technical_score, recommendation"
        ).in_("interview_id", interview_ids).order(
            "overall_score", desc=True
        ).limit(limit).execute()

        # Enrich with candidate and job info
        results = []
        for score in scores.data:
            interview = next(
                (i for i in interviews.data if i["id"] == score["interview_id"]),
                None
            )
            if interview:
                job = next((j for j in jobs.data if j["id"] == interview["job_id"]), None)

                # Get candidate profile
                profile = await supabase_service.get_profile(interview["candidate_id"])

                results.append({
                    "candidate_id": interview["candidate_id"],
                    "candidate_name": profile.get("full_name") if profile else None,
                    "job_id": interview["job_id"],
                    "job_title": job.get("title") if job else None,
                    "overall_score": score.get("overall_score"),
                    "technical_score": score.get("technical_score"),
                    "recommendation": score.get("recommendation")
                })

        return results


def create_analytics_service(supabase_client: AsyncClient) -> AnalyticsService:
    """Create an AnalyticsService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured AnalyticsService
    """
    return AnalyticsService(supabase_client)
