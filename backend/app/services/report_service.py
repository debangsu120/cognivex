"""Report Generation Service for creating interview reports."""

from typing import Dict, List, Any, Optional
from datetime import datetime

from supabase import AsyncClient
from app.exceptions import SupabaseException, AIException
from app.services.groq import groq_service


class ReportService:
    """Service for generating comprehensive interview reports."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client
        """
        self.supabase = supabase_client

    async def generate_candidate_report(
        self,
        interview_id: str,
        include_transcript: bool = True
    ) -> Dict[str, Any]:
        """Generate a candidate-facing interview report.

        Args:
            interview_id: Interview ID
            include_transcript: Whether to include full transcript

        Returns:
            Candidate report data
        """
        # Get interview with all related data
        interview = await self._get_interview_data(interview_id)
        if not interview:
            raise ValueError("Interview not found")

        # Get scores
        scores = await self.supabase.table("interview_scores").select(
            "*"
        ).eq("interview_id", interview_id).execute()

        score_data = scores.data[0] if scores.data else None

        # Get answers with questions
        answers = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).execute()

        # Build report structure
        report = {
            "report_type": "candidate",
            "generated_at": datetime.utcnow().isoformat(),
            "interview": {
                "id": interview_id,
                "status": interview.get("status"),
                "difficulty": interview.get("difficulty"),
                "duration_minutes": interview.get("duration_minutes"),
                "completed_at": interview.get("completed_at")
            },
            "job": {
                "title": interview.get("jobs", {}).get("title") if isinstance(interview.get("jobs"), dict) else "Unknown",
                "company": interview.get("jobs", {}).get("company") if isinstance(interview.get("jobs"), dict) else "Unknown"
            } if interview.get("jobs") else None,
            "overall_score": score_data.get("overall_score") if score_data else None,
            "recommendation": score_data.get("recommendation") if score_data else None,
            "summary": score_data.get("summary") if score_data else None,
            "questions": self._build_question_summary(answers.data, include_transcript),
            "strengths": score_data.get("strengths", []) if score_data else [],
            "areas_for_improvement": score_data.get("weaknesses", []) if score_data else []
        }

        return report

    async def generate_recruiter_report(
        self,
        interview_id: str,
        include_detailed_feedback: bool = True
    ) -> Dict[str, Any]:
        """Generate a recruiter/hiring manager facing report.

        Args:
            interview_id: Interview ID
            include_detailed_feedback: Whether to include detailed AI feedback

        Returns:
            Recruiter report data
        """
        # Get interview with all related data
        interview = await self._get_interview_data(interview_id)
        if not interview:
            raise ValueError("Interview not found")

        # Get scores
        scores = await self.supabase.table("interview_scores").select(
            "*"
        ).eq("interview_id", interview_id).execute()

        score_data = scores.data[0] if scores.data else None

        # Get answers with questions
        answers = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).execute()

        # Get candidate info
        candidate = await self._get_candidate_info(interview.get("candidate_id"))

        # Build comprehensive report
        report = {
            "report_type": "recruiter",
            "generated_at": datetime.utcnow().isoformat(),
            "interview_details": {
                "id": interview_id,
                "status": interview.get("status"),
                "difficulty": interview.get("difficulty"),
                "duration_minutes": interview.get("duration_minutes"),
                "started_at": interview.get("started_at"),
                "completed_at": interview.get("completed_at"),
                "created_by": interview.get("created_by")
            },
            "job_details": interview.get("jobs") if isinstance(interview.get("jobs"), dict) else None,
            "candidate": candidate,
            "scoring": {
                "overall_score": score_data.get("overall_score") if score_data else None,
                "technical_score": score_data.get("technical_score") if score_data else None,
                "communication_score": score_data.get("communication_score") if score_data else None,
                "problem_solving_score": score_data.get("problem_solving_score") if score_data else None,
                "cultural_fit_score": score_data.get("cultural_fit_score") if score_data else None,
                "recommendation": score_data.get("recommendation") if score_data else None,
                "strengths": score_data.get("strengths", []) if score_data else [],
                "weaknesses": score_data.get("weaknesses", []) if score_data else []
            },
            "question_breakdown": self._build_detailed_question_breakdown(
                answers.data,
                include_detailed_feedback
            ),
            "transcript": self._build_transcript_summary(answers.data) if include_detailed_feedback else None,
            "statistics": {
                "total_questions": len(answers.data),
                "questions_answered": len([a for a in answers.data if a.get("answer_text") or a.get("transcript")]),
                "audio_answers": len([a for a in answers.data if a.get("audio_url")]),
                "text_answers": len([a for a in answers.data if a.get("answer_text")])
            }
        }

        # Add AI-generated insights if requested
        if include_detailed_feedback:
            try:
                insights = await self._generate_ai_insights(interview_id, answers.data)
                report["ai_insights"] = insights
            except Exception:
                pass  # Don't fail if AI insights fail

        return report

    async def generate_comparison_report(
        self,
        interview_ids: List[str]
    ) -> Dict[str, Any]:
        """Generate a comparison report for multiple interviews.

        Args:
            interview_ids: List of interview IDs to compare

        Returns:
            Comparison report
        """
        interviews_data = []

        for interview_id in interview_ids:
            interview = await self._get_interview_data(interview_id)
            if interview:
                scores = await self.supabase.table("interview_scores").select(
                    "*"
                ).eq("interview_id", interview_id).execute()

                candidate = await self._get_candidate_info(interview.get("candidate_id"))

                interviews_data.append({
                    "interview_id": interview_id,
                    "candidate": candidate,
                    "overall_score": scores.data[0].get("overall_score") if scores.data else None,
                    "technical_score": scores.data[0].get("technical_score") if scores.data else None,
                    "communication_score": scores.data[0].get("communication_score") if scores.data else None,
                    "recommendation": scores.data[0].get("recommendation") if scores.data else None,
                    "status": interview.get("status")
                })

        # Calculate rankings
        ranked = sorted(
            [i for i in interviews_data if i.get("overall_score")],
            key=lambda x: x["overall_score"],
            reverse=True
        )

        return {
            "report_type": "comparison",
            "generated_at": datetime.utcnow().isoformat(),
            "total_interviews": len(interviews_data),
            "interviews": interviews_data,
            "rankings": ranked,
            "statistics": self._calculate_comparison_statistics(interviews_data)
        }

    async def _get_interview_data(self, interview_id: str) -> Optional[Dict]:
        """Get complete interview data.

        Args:
            interview_id: Interview ID

        Returns:
            Interview data or None
        """
        response = await self.supabase.table("interviews").select(
            "*, jobs(*), interview_questions(*)"
        ).eq("id", interview_id).execute()

        return response.data[0] if response.data else None

    async def _get_candidate_info(self, candidate_id: Optional[str]) -> Optional[Dict]:
        """Get candidate information.

        Args:
            candidate_id: Candidate user ID

        Returns:
            Candidate info or None
        """
        if not candidate_id:
            return None

        response = await self.supabase.table("users").select(
            "id, email, full_name, avatar_url"
        ).eq("id", candidate_id).execute()

        return response.data[0] if response.data else None

    def _build_question_summary(
        self,
        answers: List[Dict],
        include_transcript: bool
    ) -> List[Dict]:
        """Build question summary for candidate report.

        Args:
            answers: List of answers
            include_transcript: Whether to include full transcript

        Returns:
            Question summaries
        """
        summary = []

        for answer in answers:
            question = answer.get("interview_questions", {})
            summary.append({
                "question_number": question.get("question_order"),
                "question": question.get("question_text"),
                "category": question.get("category"),
                "skill_tested": question.get("skill"),
                "score": answer.get("score"),
                "feedback": answer.get("feedback"),
                "transcript": answer.get("transcript") if include_transcript else None
            })

        return summary

    def _build_detailed_question_breakdown(
        self,
        answers: List[Dict],
        include_feedback: bool
    ) -> List[Dict]:
        """Build detailed question breakdown for recruiter report.

        Args:
            answers: List of answers
            include_feedback: Whether to include detailed feedback

        Returns:
            Detailed breakdown
        """
        breakdown = []

        for answer in answers:
            question = answer.get("interview_questions", {})
            item = {
                "question_number": question.get("question_order"),
                "question": question.get("question_text"),
                "category": question.get("category"),
                "difficulty": question.get("difficulty"),
                "skill_tested": question.get("skill"),
                "answer_type": "audio" if answer.get("audio_url") else "text",
                "answer_text": answer.get("answer_text"),
                "transcript": answer.get("transcript"),
                "score": answer.get("score"),
                "technical_accuracy": answer.get("technical_accuracy"),
                "communication_clarity": answer.get("communication_clarity")
            }

            if include_feedback:
                item["feedback"] = answer.get("feedback")
                item["strengths"] = answer.get("strengths", [])
                item["improvements"] = answer.get("improvements", [])
                item["concepts_detected"] = answer.get("concepts_detected", [])
                item["concepts_missing"] = answer.get("concepts_missing", [])

            breakdown.append(item)

        return breakdown

    def _build_transcript_summary(self, answers: List[Dict]) -> List[Dict]:
        """Build transcript summary.

        Args:
            answers: List of answers

        Returns:
            Transcript entries
        """
        transcript = []

        for answer in answers:
            question = answer.get("interview_questions", {})
            content = answer.get("transcript") or answer.get("answer_text")

            if content:
                transcript.append({
                    "question_number": question.get("question_order"),
                    "question": question.get("question_text"),
                    "answer": content,
                    "audio_url": answer.get("audio_url")
                })

        return transcript

    async def _generate_ai_insights(
        self,
        interview_id: str,
        answers: List[Dict]
    ) -> Dict[str, Any]:
        """Generate AI-powered insights for the interview.

        Args:
            interview_id: Interview ID
            answers: List of answers

        Returns:
            AI insights
        """
        # Build summary for AI
        answers_summary = "\n".join([
            f"Q{a.get('interview_questions', {}).get('question_order', '?')}: "
            f"{a.get('interview_questions', {}).get('question_text', '')}\n"
            f"A: {a.get('transcript') or a.get('answer_text', '')}\n"
            f"Score: {a.get('score', 'N/A')}"
            for a in answers
        ])

        prompt = f"""Provide additional insights for this interview based on all answers.

Interview Answers:
{answers_summary}

Return a JSON object with this exact format:
{{
    "candidate_profile": "brief profile description",
    "key_strengths": ["strength1", "strength2"],
    "development_areas": ["area1", "area2"],
    "interview_style": "assessment of how candidate performed",
    "risk_factors": ["potential concern1"],
    "positive_indicators": ["positive sign1"],
    "suggested_assessment_areas": ["areas to explore in next round"]
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await groq_service.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR professional. Provide deep insights from interview performance."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            import json
            content = response.choices[0].message.content

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {}

        except Exception:
            return {}

    def _calculate_comparison_statistics(
        self,
        interviews: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate statistics for comparison.

        Args:
            interviews: List of interview data

        Returns:
            Statistics
        """
        scores = [i.get("overall_score") for i in interviews if i.get("overall_score")]

        if not scores:
            return {}

        return {
            "average_score": round(sum(scores) / len(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "score_range": max(scores) - min(scores),
            "total_candidates": len(interviews),
            "hire_recommendations": len([i for i in interviews if i.get("recommendation") in ["hire", "strong_hire"]]),
            "no_hire_recommendations": len([i for i in interviews if i.get("recommendation") in ["no_hire", "strong_no_hire"]]),
            "uncertain": len([i for i in interviews if i.get("recommendation") == "uncertain"])
        }

    async def export_report_as_json(
        self,
        interview_id: str,
        report_type: str = "recruiter"
    ) -> Dict[str, Any]:
        """Export report as JSON-serializable format.

        Args:
            interview_id: Interview ID
            report_type: Type of report to generate

        Returns:
            Exportable report data
        """
        if report_type == "candidate":
            return await self.generate_candidate_report(interview_id)
        else:
            return await self.generate_recruiter_report(interview_id)

    async def get_interview_transcript(
        self,
        interview_id: str
    ) -> List[Dict[str, Any]]:
        """Get full transcript for an interview.

        Args:
            interview_id: Interview ID

        Returns:
            List of transcript entries
        """
        answers = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).execute()

        transcript = []

        for answer in answers.data:
            question = answer.get("interview_questions", {})
            content = answer.get("transcript") or answer.get("answer_text")

            transcript.append({
                "question_number": question.get("question_order"),
                "question": question.get("question_text"),
                "answer": content,
                "audio_url": answer.get("audio_url"),
                "score": answer.get("score"),
                "timestamp": answer.get("created_at")
            })

        return transcript


def create_report_service(supabase_client: AsyncClient) -> ReportService:
    """Create a ReportService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured ReportService instance
    """
    return ReportService(supabase_client)
