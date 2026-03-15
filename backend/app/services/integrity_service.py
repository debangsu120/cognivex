"""
Interview Integrity Service

Monitors interview sessions for suspicious patterns and anomalies
to maintain fair and trustworthy AI interviews.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from supabase import AsyncClient


class IntegrityService:
    """Service for monitoring interview integrity."""

    def __init__(self, supabase_client: AsyncClient):
        self.supabase = supabase_client

    async def analyze_session_patterns(
        self,
        interview_id: str
    ) -> Dict[str, Any]:
        """Analyze interview session for suspicious patterns.

        Args:
            interview_id: Interview ID to analyze

        Returns:
            Analysis results with flags and integrity score
        """
        # Get all answers for this interview
        questions = await self.supabase.table("interview_questions").select(
            "id, question_text, question_order"
        ).eq("interview_id", interview_id).order("question_order").execute()

        answers = await self.supabase.table("interview_answers").select(
            "question_id, answer_text, transcript, created_at"
        ).in_(
            "question_id",
            [q["id"] for q in questions.data]
        ).execute()

        if not answers.data:
            return {
                "interview_id": interview_id,
                "integrity_score": None,
                "flags": {},
                "message": "No answers to analyze"
            }

        # Analyze patterns
        flags = {}
        response_times = []
        pause_counts = []
        answer_lengths = []
        repeated_answers = []

        # Check for repeated answers
        answer_texts = [a.get("answer_text") or a.get("transcript", "") for a in answers.data]
        for i, text1 in enumerate(answer_texts):
            for j, text2 in enumerate(answer_texts[i+1:], i+1):
                if text1 and text2 and len(text1) > 50:
                    # Simple similarity check
                    similarity = self._text_similarity(text1, text2)
                    if similarity > 0.8:
                        repeated_answers.append({
                            "question_pair": (i+1, j+1),
                            "similarity": round(similarity, 2)
                        })

        # Check answer lengths (too short might indicate lack of effort)
        short_answers = sum(1 for t in answer_texts if t and len(t.strip()) < 30)
        if short_answers > len(answer_texts) * 0.5:
            flags["excessive_short_answers"] = {
                "count": short_answers,
                "severity": "high"
            }

        # Check for very long pauses (we'd need timing data)
        # For now, flag if answers are unusually long (might indicate reading)
        long_answers = sum(1 for t in answer_texts if t and len(t) > 2000)
        if long_answers > len(answer_texts) * 0.7:
            flags["unusually_long_answers"] = {
                "count": long_answers,
                "severity": "medium",
                "note": "May indicate reading from external source"
            }

        # Repeated answers flag
        if len(repeated_answers) > 2:
            flags["repeated_answers"] = {
                "count": len(repeated_answers),
                "severity": "high",
                "details": repeated_answers[:5]  # First 5
            }
        elif repeated_answers:
            flags["some_repeated_patterns"] = {
                "count": len(repeated_answers),
                "severity": "low",
                "details": repeated_answers[:3]
            }

        # Calculate integrity score
        integrity_score = self._calculate_integrity_score(flags, len(answers.data))

        return {
            "interview_id": interview_id,
            "total_answers": len(answers.data),
            "integrity_score": integrity_score,
            "flags": flags,
            "severity": self._get_severity(integrity_score),
            "recommendation": self._get_recommendation(integrity_score, flags)
        }

    async def record_session_metrics(
        self,
        interview_id: str,
        question_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record session metrics for an answer.

        Args:
            interview_id: Interview ID
            question_id: Question ID
            metrics: Dictionary of metrics to record

        Returns:
            Recorded metrics
        """
        data = {
            "interview_id": interview_id,
            "question_id": question_id,
            "response_time_seconds": metrics.get("response_time_seconds"),
            "pause_count": metrics.get("pause_count", 0),
            "total_pause_duration": metrics.get("total_pause_duration", 0),
            "word_count": metrics.get("word_count"),
            "speech_rate_words_per_minute": metrics.get("speech_rate"),
            "audio_duration_seconds": metrics.get("audio_duration")
        }

        # Calculate integrity for this answer
        integrity_score = self._calculate_answer_integrity(metrics)
        data["integrity_score"] = integrity_score
        data["flags"] = self._flag_answer_anomalies(metrics)

        result = await self.supabase.table("interview_session_metrics").insert(data).execute()

        return result.data[0] if result.data else {"status": "error"}

    async def get_interview_integrity_history(
        self,
        interview_id: str
    ) -> Dict[str, Any]:
        """Get integrity history for an interview.

        Args:
            interview_id: Interview ID

        Returns:
            Integrity history with trends
        """
        metrics = await self.supabase.table("interview_session_metrics").select(
            "*"
        ).eq("interview_id", interview_id).order("created_at").execute()

        if not metrics.data:
            return {
                "interview_id": interview_id,
                "has_metrics": False,
                "message": "No session metrics recorded"
            }

        integrity_scores = [m["integrity_score"] for m in metrics.data if m.get("integrity_score")]
        avg_integrity = sum(integrity_scores) / len(integrity_scores) if integrity_scores else None

        # Check for declining integrity (might indicate cheating)
        trend = "stable"
        if len(integrity_scores) >= 3:
            first_third = integrity_scores[:len(integrity_scores)//3]
            last_third = integrity_scores[-len(integrity_scores)//3:]

            first_avg = sum(first_third) / len(first_third)
            last_avg = sum(last_third) / len(last_third)

            if first_avg - last_avg > 20:
                trend = "declining"
            elif last_avg - first_avg > 20:
                trend = "improving"

        return {
            "interview_id": interview_id,
            "has_metrics": True,
            "total_questions": len(metrics.data),
            "average_integrity": round(avg_integrity, 1) if avg_integrity else None,
            "integrity_trend": trend,
            "question_metrics": [
                {
                    "question_order": i + 1,
                    "integrity_score": m["integrity_score"],
                    "word_count": m.get("word_count"),
                    "flags": m.get("flags")
                }
                for i, m in enumerate(metrics.data)
            ]
        }

    def _calculate_integrity_score(
        self,
        flags: Dict[str, Any],
        total_answers: int
    ) -> float:
        """Calculate overall integrity score (0-100).

        Args:
            flags: Dictionary of detected flags
            total_answers: Total number of answers

        Returns:
            Integrity score
        """
        if total_answers == 0:
            return 100.0

        score = 100.0

        # Deduct for high severity flags
        high_severity = sum(
            1 for f in flags.values()
            if isinstance(f, dict) and f.get("severity") == "high"
        )
        score -= high_severity * 25

        # Deduct for medium severity flags
        medium_severity = sum(
            1 for f in flags.values()
            if isinstance(f, dict) and f.get("severity") == "medium"
        )
        score -= medium_severity * 10

        # Deduct for low severity flags
        low_severity = sum(
            1 for f in flags.values()
            if isinstance(f, dict) and f.get("severity") == "low"
        )
        score -= low_severity * 5

        return max(0.0, min(100.0, score))

    def _calculate_answer_integrity(self, metrics: Dict[str, Any]) -> float:
        """Calculate integrity score for a single answer.

        Args:
            metrics: Answer metrics

        Returns:
            Integrity score (0-100)
        """
        score = 100.0

        # Check for suspiciously perfect timing (might be scripted)
        response_time = metrics.get("response_time_seconds", 0)
        if 0 < response_time < 2:
            score -= 10  # Too quick might indicate memorized answer

        # Check for unusual speech rate
        speech_rate = metrics.get("speech_rate", 0)
        if speech_rate > 200 or speech_rate < 50:
            score -= 15

        # Check for abnormal pause patterns
        pause_count = metrics.get("pause_count", 0)
        if pause_count > 10:
            score -= 20

        return max(0.0, min(100.0, score))

    def _flag_answer_anomalies(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Flag anomalies in answer metrics.

        Args:
            metrics: Answer metrics

        Returns:
            Dictionary of flags
        """
        flags = {}

        # Unusually quick response
        if 0 < metrics.get("response_time_seconds", 0) < 2:
            flags["very_quick_response"] = "Response time unusually short"

        # Unusual speech rate
        speech_rate = metrics.get("speech_rate", 0)
        if speech_rate > 200:
            flags["fast_speech"] = "Speech rate unusually fast"
        elif speech_rate > 0 and speech_rate < 50:
            flags["slow_speech"] = "Speech rate unusually slow"

        # Many pauses
        if metrics.get("pause_count", 0) > 10:
            flags["many_pauses"] = "Unusually many pauses detected"

        # Very short answer
        word_count = metrics.get("word_count", 0)
        if 0 < word_count < 10:
            flags["very_short_answer"] = "Answer contains very few words"

        return flags

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0

        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _get_severity(self, score: float) -> str:
        """Get severity label from score.

        Args:
            score: Integrity score

        Returns:
            Severity label
        """
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        else:
            return "high"

    def _get_recommendation(
        self,
        score: float,
        flags: Dict[str, Any]
    ) -> str:
        """Get recommendation based on integrity analysis.

        Args:
            score: Integrity score
            flags: Detected flags

        Returns:
            Recommendation text
        """
        if score >= 80 and not flags:
            return "No concerns - interview appears legitimate"

        high_severity = sum(
            1 for f in flags.values()
            if isinstance(f, dict) and f.get("severity") == "high"
        )

        if high_severity > 0:
            return "Manual review recommended - multiple high-severity flags detected"

        if score >= 60:
            return "Interview likely valid with minor concerns"

        return "Further investigation recommended"


def create_integrity_service(supabase_client: AsyncClient) -> IntegrityService:
    """Create an IntegrityService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured IntegrityService
    """
    return IntegrityService(supabase_client)
