"""
Skill Profile Service

Manages dynamic candidate skill portfolios that evolve over time
based on interview performance.
"""

from typing import Dict, List, Any, Optional
from supabase import AsyncClient


class SkillProfileService:
    """Service for managing candidate skill profiles."""

    def __init__(self, supabase_client: AsyncClient):
        self.supabase = supabase_client

    async def update_skill_profile(
        self,
        user_id: str,
        skill_name: str,
        score: float
    ) -> Dict[str, Any]:
        """Update skill profile with a new score.

        Args:
            user_id: User ID
            skill_name: Name of the skill
            score: New score (0-10)

        Returns:
            Updated skill profile
        """
        # Check if profile exists
        existing = await self.supabase.table("skill_profiles").select(
            "*"
        ).eq("user_id", user_id).eq("skill_name", skill_name.lower()).execute()

        if existing.data:
            profile = existing.data[0]
            score_history = profile.get("score_history", [])
            score_history.append(score)

            # Calculate consistency (lower variance = more consistent)
            if len(score_history) > 1:
                avg = sum(score_history) / len(score_history)
                variance = sum((s - avg) ** 2 for s in score_history) / len(score_history)
                consistency = max(0, 100 - (variance * 10))  # Convert to 0-100 scale
            else:
                consistency = 100

            # Update
            data = {
                "score_history": score_history[-10:],  # Keep last 10
                "latest_score": score,
                "consistency_score": round(consistency, 1),
                "interview_count": profile.get("interview_count", 0) + 1,
                "last_updated": "now()"
            }

            result = await self.supabase.table("skill_profiles").update(
                data
            ).eq("id", profile["id"]).execute()

            return result.data[0] if result.data else {"status": "error"}
        else:
            # Create new
            data = {
                "user_id": user_id,
                "skill_name": skill_name.lower(),
                "score_history": [score],
                "latest_score": score,
                "consistency_score": 100,
                "interview_count": 1
            }

            result = await self.supabase.table("skill_profiles").insert(data).execute()

            return result.data[0] if result.data else {"status": "error"}

    async def get_skill_profile(
        self,
        user_id: str,
        skill_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get skill profile for a specific skill.

        Args:
            user_id: User ID
            skill_name: Skill name

        Returns:
            Skill profile or None
        """
        result = await self.supabase.table("skill_profiles").select(
            "*"
        ).eq("user_id", user_id).eq("skill_name", skill_name.lower()).execute()

        return result.data[0] if result.data else None

    async def get_user_skill_profile(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get all skill profiles for a user.

        Args:
            user_id: User ID

        Returns:
            User's skill portfolio
        """
        result = await self.supabase.table("skill_profiles").select(
            "*"
        ).eq("user_id", user_id).order("latest_score", desc=True).execute()

        skills = []
        for profile in result.data:
            skills.append({
                "skill": profile["skill_name"],
                "latest_score": profile["latest_score"],
                "consistency_score": profile["consistency_score"],
                "interview_count": profile["interview_count"],
                "score_history": profile.get("score_history", []),
                "first_seen": profile["first_seen"],
                "last_updated": profile["last_updated"]
            })

        # Calculate overall metrics
        if skills:
            avg_score = sum(s["latest_score"] for s in skills) / len(skills)
            avg_consistency = sum(s["consistency_score"] for s in skills) / len(skills)
        else:
            avg_score = avg_consistency = 0

        return {
            "user_id": user_id,
            "total_skills": len(skills),
            "skills": skills,
            "average_score": round(avg_score, 1),
            "average_consistency": round(avg_consistency, 1)
        }

    async def get_skill_trend(
        self,
        user_id: str,
        skill_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get skill trend over time.

        Args:
            user_id: User ID
            skill_name: Skill name

        Returns:
            Trend data or None
        """
        profile = await self.get_skill_profile(user_id, skill_name)

        if not profile:
            return None

        score_history = profile.get("score_history", [])

        if len(score_history) < 2:
            return {
                "skill": skill_name,
                "trend": "insufficient_data",
                "scores": score_history,
                "total_interviews": len(score_history)
            }

        # Calculate trend
        first_half = score_history[:len(score_history)//2]
        second_half = score_history[len(score_history)//2:]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if second_avg - first_avg > 1:
            trend = "improving"
        elif first_avg - second_avg > 1:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "skill": skill_name,
            "trend": trend,
            "improvement": round(second_avg - first_avg, 1),
            "scores": score_history,
            "total_interviews": len(score_history),
            "latest_score": score_history[-1],
            "best_score": max(score_history),
            "consistency": profile.get("consistency_score", 0)
        }

    async def get_top_skills(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get user's top performing skills.

        Args:
            user_id: User ID
            limit: Number of skills to return

        Returns:
            Top skills list
        """
        result = await self.supabase.table("skill_profiles").select(
            "*"
        ).eq("user_id", user_id).order("latest_score", desc=True).limit(limit).execute()

        return [
            {
                "skill": r["skill_name"],
                "score": r["latest_score"],
                "consistency": r["consistency_score"],
                "interviews": r["interview_count"]
            }
            for r in result.data
        ]

    async def get_skills_needing_improvement(
        self,
        user_id: str,
        threshold: float = 6.0
    ) -> List[Dict[str, Any]]:
        """Get skills that may need improvement.

        Args:
            user_id: User ID
            threshold: Score threshold

        Returns:
            Skills below threshold
        """
        result = await self.supabase.table("skill_profiles").select(
            "*"
        ).eq("user_id", user_id).lte("latest_score", threshold).execute()

        return [
            {
                "skill": r["skill_name"],
                "score": r["latest_score"],
                "trend": await self.get_skill_trend(user_id, r["skill_name"]),
                "interviews": r["interview_count"]
            }
            for r in result.data
        ]

    async def compare_candidates(
        self,
        candidate_ids: List[str],
        skill_name: str
    ) -> List[Dict[str, Any]]:
        """Compare multiple candidates on a specific skill.

        Args:
            candidate_ids: List of candidate IDs
            skill_name: Skill to compare

        Returns:
            Comparison results
        """
        results = []

        for user_id in candidate_ids:
            profile = await self.get_skill_profile(user_id, skill_name)

            if profile:
                results.append({
                    "user_id": user_id,
                    "skill": skill_name,
                    "score": profile["latest_score"],
                    "consistency": profile["consistency_score"],
                    "interviews": profile["interview_count"]
                })
            else:
                results.append({
                    "user_id": user_id,
                    "skill": skill_name,
                    "score": None,
                    "note": "No data available"
                })

        # Sort by score
        results.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)

        # Add rank
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return results


def create_skill_profile_service(supabase_client: AsyncClient) -> SkillProfileService:
    """Create a SkillProfileService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured SkillProfileService
    """
    return SkillProfileService(supabase_client)
