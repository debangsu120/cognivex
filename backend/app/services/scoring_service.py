"""Scoring Service for aggregating and calculating interview scores."""

from typing import Dict, List, Any, Optional

from supabase import AsyncClient
from app.exceptions import SupabaseException


# Default skill weights for scoring
DEFAULT_SKILL_WEIGHTS = {
    "technical": 0.40,
    "communication": 0.25,
    "problem_solving": 0.20,
    "cultural_fit": 0.15
}

# Question category to skill mapping
CATEGORY_SKILL_MAP = {
    "concept": "technical",
    "application": "problem_solving",
    "advanced": "technical",
    "behavioral": "cultural_fit",
    "communication": "communication"
}


class ScoringService:
    """Service for calculating and aggregating interview scores."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client
        """
        self.supabase = supabase_client

    async def calculate_question_score(
        self,
        answer_id: str
    ) -> Dict[str, Any]:
        """Calculate score for a single answer.

        Args:
            answer_id: Answer ID

        Returns:
            Score breakdown
        """
        # Get answer with question details
        answer = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("id", answer_id).execute()

        if not answer.data:
            raise ValueError("Answer not found")

        answer_data = answer.data[0]
        question = answer_data.get("interview_questions", {})

        # Extract scores
        score = answer_data.get("score", 0)
        technical_accuracy = answer_data.get("technical_accuracy", score)
        communication_clarity = answer_data.get("communication_clarity", score)

        # Determine skill category from question
        category = question.get("category", "application")
        skill_type = CATEGORY_SKILL_MAP.get(category, "technical")

        return {
            "answer_id": answer_id,
            "overall_score": score,
            "skill_type": skill_type,
            "scores": {
                "technical": technical_accuracy,
                "communication": communication_clarity,
                "problem_solving": score if skill_type == "problem_solving" else technical_accuracy,
                "cultural_fit": score if skill_type == "cultural_fit" else technical_accuracy
            }
        }

    async def calculate_interview_score(
        self,
        interview_id: str,
        skill_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Calculate overall interview score with skill breakdown.

        Args:
            interview_id: Interview ID
            skill_weights: Optional custom weights for skills

        Returns:
            Comprehensive score breakdown
        """
        weights = skill_weights or DEFAULT_SKILL_WEIGHTS

        # Get all answers for this interview
        answers = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).execute()

        if not answers.data:
            raise ValueError("No answers found for this interview")

        # Aggregate scores by skill type
        skill_scores: Dict[str, List[float]] = {
            "technical": [],
            "communication": [],
            "problem_solving": [],
            "cultural_fit": []
        }

        all_scores = []

        for answer in answers.data:
            question = answer.get("interview_questions", {})
            category = question.get("category", "application")
            skill_type = CATEGORY_SKILL_MAP.get(category, "technical")

            score = answer.get("score", 0)
            technical = answer.get("technical_accuracy", score)
            communication = answer.get("communication_clarity", score)

            # Add to appropriate skill bucket
            skill_scores[skill_type].append(score)

            # Also add to other categories with same score (for averaging)
            if skill_type != "technical":
                skill_scores["technical"].append(technical)
            if skill_type != "communication":
                skill_scores["communication"].append(communication)

            all_scores.append(score)

        # Calculate weighted average for each skill
        skill_averages = {}
        for skill, scores in skill_scores.items():
            if scores:
                skill_averages[skill] = sum(scores) / len(scores)
            else:
                skill_averages[skill] = 0

        # Calculate weighted overall score
        overall_score = sum(
            skill_averages[skill] * weight
            for skill, weight in weights.items()
        )

        # Calculate question-level statistics
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        max_score = max(all_scores) if all_scores else 0
        min_score = min(all_scores) if all_scores else 0

        # Determine recommendation
        recommendation = self._determine_recommendation(overall_score)

        # Get strengths and weaknesses from individual answers
        strengths, weaknesses = await self._aggregate_feedback(interview_id)

        return {
            "interview_id": interview_id,
            "overall_score": round(overall_score, 2),
            "skill_scores": {
                "technical": round(skill_averages.get("technical", 0), 2),
                "communication": round(skill_averages.get("communication", 0), 2),
                "problem_solving": round(skill_averages.get("problem_solving", 0), 2),
                "cultural_fit": round(skill_averages.get("cultural_fit", 0), 2)
            },
            "question_statistics": {
                "total_questions": len(all_scores),
                "average_score": round(avg_score, 2),
                "highest_score": round(max_score, 2),
                "lowest_score": round(min_score, 2),
                "score_distribution": self._calculate_distribution(all_scores)
            },
            "weights_used": weights,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendation": recommendation
        }

    def _calculate_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution.

        Args:
            scores: List of scores

        Returns:
            Distribution breakdown
        """
        distribution = {
            "excellent": 0,  # 90-100
            "good": 0,       # 70-89
            "fair": 0,       # 50-69
            "poor": 0        # 0-49
        }

        for score in scores:
            if score >= 90:
                distribution["excellent"] += 1
            elif score >= 70:
                distribution["good"] += 1
            elif score >= 50:
                distribution["fair"] += 1
            else:
                distribution["poor"] += 1

        return distribution

    def _determine_recommendation(self, overall_score: float) -> str:
        """Determine hiring recommendation based on score.

        Args:
            overall_score: Overall interview score

        Returns:
            Recommendation string
        """
        if overall_score >= 80:
            return "strong_hire"
        elif overall_score >= 65:
            return "hire"
        elif overall_score >= 50:
            return "uncertain"
        elif overall_score >= 35:
            return "no_hire"
        else:
            return "strong_no_hire"

    async def _aggregate_feedback(
        self,
        interview_id: str
    ) -> tuple[List[str], List[str]]:
        """Aggregate strengths and weaknesses from all answers.

        Args:
            interview_id: Interview ID

        Returns:
            Tuple of (strengths, weaknesses)
        """
        answers = await self.supabase.table("interview_answers").select(
            "strengths, improvements"
        ).eq("interview_questions.interview_id", interview_id).execute()

        if not answers.data:
            return [], []

        strengths_set = set()
        weaknesses_set = set()

        for answer in answers.data:
            # Aggregate strengths
            for strength in answer.get("strengths", []):
                if strength:
                    strengths_set.add(strength)

            # Aggregate improvements as weaknesses
            for improvement in answer.get("improvements", []):
                if improvement:
                    weaknesses_set.add(improvement)

        # Limit to top 5 each
        return list(strengths_set)[:5], list(weaknesses_set)[:5]

    async def save_interview_score(
        self,
        interview_id: str,
        score_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save calculated scores to database.

        Args:
            interview_id: Interview ID
            score_data: Score data to save

        Returns:
            Saved score record
        """
        # Check if score already exists
        existing = await self.supabase.table("interview_scores").select(
            "id"
        ).eq("interview_id", interview_id).execute()

        data = {
            "interview_id": interview_id,
            "overall_score": score_data.get("overall_score"),
            "technical_score": score_data.get("skill_scores", {}).get("technical"),
            "communication_score": score_data.get("skill_scores", {}).get("communication"),
            "problem_solving_score": score_data.get("skill_scores", {}).get("problem_solving"),
            "cultural_fit_score": score_data.get("skill_scores", {}).get("cultural_fit"),
            "strengths": score_data.get("strengths", []),
            "weaknesses": score_data.get("weaknesses", []),
            "summary": self._generate_summary(score_data),
            "recommendation": score_data.get("recommendation", "uncertain")
        }

        if existing.data:
            # Update existing
            response = await self.supabase.table("interview_scores").update(
                {k: v for k, v in data.items() if v is not None}
            ).eq("interview_id", interview_id).execute()
        else:
            # Insert new
            response = await self.supabase.table("interview_scores").insert(data).execute()

        if not response.data:
            raise SupabaseException("Failed to save interview score")

        return response.data[0]

    def _generate_summary(self, score_data: Dict[str, Any]) -> str:
        """Generate a text summary from score data.

        Args:
            score_data: Score breakdown

        Returns:
            Summary text
        """
        overall = score_data.get("overall_score", 0)
        skills = score_data.get("skill_scores", {})
        recommendation = score_data.get("recommendation", "uncertain")

        recommendation_text = {
            "strong_hire": "strongly recommend hiring",
            "hire": "recommend hiring",
            "uncertain": "need more evaluation",
            "no_hire": "recommend not hiring",
            "strong_no_hire": "strongly recommend not hiring"
        }.get(recommendation, "need more evaluation")

        # Find strongest and weakest skills
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
        strongest = sorted_skills[0] if sorted_skills else ("technical", 0)
        weakest = sorted_skills[-1] if sorted_skills else ("technical", 0)

        return (
            f"Candidate scored {overall:.0f}% overall, with strongest performance in "
            f"{strongest[0]} ({strongest[1]:.0f}%) and room for improvement in "
            f"{weakest[0]} ({weakest[1]:.0f}%). Based on the interview performance, "
            f"we {recommendation_text}."
        )

    async def recalculate_all_scores(self, interview_id: str) -> Dict[str, Any]:
        """Recalculate all scores for an interview.

        Args:
            interview_id: Interview ID

        Returns:
            Updated score data
        """
        # Calculate new scores
        score_data = await self.calculate_interview_score(interview_id)

        # Save to database
        saved_score = await self.save_interview_score(interview_id, score_data)

        return {
            **saved_score,
            "skill_scores": score_data["skill_scores"],
            "question_statistics": score_data["question_statistics"]
        }

    async def get_skill_breakdown(
        self,
        interview_id: str
    ) -> Dict[str, Any]:
        """Get detailed skill breakdown for an interview.

        Args:
            interview_id: Interview ID

        Returns:
            Skill breakdown with question-level details
        """
        # Get all answers
        answers = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).execute()

        # Group by skill type
        skill_questions: Dict[str, List[Dict]] = {
            "technical": [],
            "communication": [],
            "problem_solving": [],
            "cultural_fit": []
        }

        for answer in answers.data:
            question = answer.get("interview_questions", {})
            category = question.get("category", "application")
            skill_type = CATEGORY_SKILL_MAP.get(category, "technical")

            skill_questions[skill_type].append({
                "question_id": question.get("id"),
                "question_text": question.get("question_text"),
                "score": answer.get("score", 0),
                "skill_category": category
            })

        # Calculate averages
        breakdown = {}
        for skill, questions in skill_questions.items():
            if questions:
                avg = sum(q["score"] for q in questions) / len(questions)
                breakdown[skill] = {
                    "average_score": round(avg, 2),
                    "question_count": len(questions),
                    "questions": questions
                }
            else:
                breakdown[skill] = {
                    "average_score": 0,
                    "question_count": 0,
                    "questions": []
                }

        return breakdown


def create_scoring_service(supabase_client: AsyncClient) -> ScoringService:
    """Create a ScoringService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured ScoringService instance
    """
    return ScoringService(supabase_client)
