"""Answer Evaluation Service for AI-powered interview answer assessment."""

from typing import List, Dict, Any, Optional

from supabase import AsyncClient
from app.exceptions import AIException
from app.services.groq import groq_service


class EvaluationService:
    """Service for evaluating candidate interview answers using AI."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client
        """
        self.supabase = supabase_client

    async def evaluate_answer(
        self,
        question_id: str,
        transcript: Optional[str] = None,
        answer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate a candidate's answer to a question.

        Args:
            question_id: Question ID to evaluate
            transcript: Speech-to-text transcript (if audio answer)
            answer_text: Text answer (if typed answer)

        Returns:
            Evaluation result with score and feedback
        """
        # Get question details
        question = await self.supabase.table("interview_questions").select(
            "*, interviews(job_id, jobs(*))"
        ).eq("id", question_id).execute()

        if not question.data:
            raise ValueError("Question not found")

        question_data = question.data[0]
        question_text = question_data.get("question_text", "")

        # Get expected concepts from question metadata
        expected_concepts = question_data.get("expected_concepts", [])

        # Get job skills
        interview_data = question_data.get("interviews", {})
        job_data = interview_data.get("jobs", {}) if isinstance(interview_data, dict) else {}
        skills_required = job_data.get("skills_required", [])

        # Use whichever answer is available
        answer_content = transcript or answer_text or ""

        if not answer_content:
            raise ValueError("No answer content provided for evaluation")

        # Evaluate using AI
        evaluation = await self._evaluate_with_ai(
            question=question_text,
            answer=answer_content,
            expected_concepts=expected_concepts,
            skills_required=skills_required
        )

        return evaluation

    async def _evaluate_with_ai(
        self,
        question: str,
        answer: str,
        expected_concepts: List[str],
        skills_required: List[str]
    ) -> Dict[str, Any]:
        """Evaluate answer using AI with detailed analysis.

        Args:
            question: The interview question
            answer: Candidate's answer
            expected_concepts: Expected concepts to check
            skills_required: Required skills from job

        Returns:
            Detailed evaluation result
        """
        skills_str = ", ".join(skills_required) if skills_required else "general"
        concepts_str = ", ".join(expected_concepts) if expected_concepts else "not specified"

        prompt = f"""You are an expert technical interviewer. Evaluate the following interview answer carefully.

Question: {question}

Expected Concepts: {concepts_str}

Required Skills: {skills_str}

Candidate's Answer: {answer}

Evaluate this answer thoroughly and return a JSON object with this exact format:
{{
    "score": 0-100,
    "technical_accuracy": 0-100,
    "completeness": 0-100,
    "communication_clarity": 0-100,
    "concepts_detected": ["concept1", "concept2"],
    "concepts_missing": ["concept1", "concept2"],
    "feedback": "constructive feedback paragraph",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"],
    "follow_up_suggestions": ["suggestion1"]
}}

Be strict but fair. Consider:
- Technical accuracy of the answer
- How well it addresses the question
- Clarity of communication
- Whether expected concepts are covered
- Completeness of the answer

Return ONLY valid JSON, no other text."""

        try:
            response = await groq_service.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical interviewer. Provide fair, constructive, and detailed evaluation."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            import json
            content = response.choices[0].message.content

            try:
                evaluation = json.loads(content)
                return self._normalize_evaluation(evaluation)
            except json.JSONDecodeError:
                return self._fallback_evaluation()

        except Exception as e:
            raise AIException(f"Failed to evaluate answer: {str(e)}")

    def _normalize_evaluation(self, evaluation: Dict) -> Dict[str, Any]:
        """Normalize evaluation to ensure all fields are present.

        Args:
            evaluation: Raw evaluation from AI

        Returns:
            Normalized evaluation
        """
        return {
            "score": max(0, min(100, evaluation.get("score", 50))),
            "technical_accuracy": max(0, min(100, evaluation.get("technical_accuracy", 50))),
            "completeness": max(0, min(100, evaluation.get("completeness", 50))),
            "communication_clarity": max(0, min(100, evaluation.get("communication_clarity", 50))),
            "concepts_detected": evaluation.get("concepts_detected", []),
            "concepts_missing": evaluation.get("concepts_missing", []),
            "feedback": evaluation.get("feedback", "Evaluation completed."),
            "strengths": evaluation.get("strengths", []),
            "improvements": evaluation.get("improvements", []),
            "follow_up_suggestions": evaluation.get("follow_up_suggestions", [])
        }

    def _fallback_evaluation(self) -> Dict[str, Any]:
        """Return a fallback evaluation if AI parsing fails.

        Returns:
            Default evaluation
        """
        return {
            "score": 50,
            "technical_accuracy": 50,
            "completeness": 50,
            "communication_clarity": 50,
            "concepts_detected": [],
            "concepts_missing": [],
            "feedback": "Unable to evaluate answer - please review manually",
            "strengths": [],
            "improvements": ["Consider providing more detailed answers"],
            "follow_up_suggestions": []
        }

    async def analyze_transcript(
        self,
        interview_id: str
    ) -> Dict[str, Any]:
        """Analyze full interview transcript for overall insights.

        Args:
            interview_id: Interview ID

        Returns:
            Transcript analysis
        """
        # Get all answers with transcripts
        answers = await self.supabase.table("interview_answers").select(
            "*, interview_questions(*)"
        ).eq("interview_questions.interview_id", interview_id).execute()

        if not answers.data:
            raise ValueError("No answers found for this interview")

        # Build transcript
        transcript_parts = []
        for answer in answers.data:
            question = answer.get("interview_questions", {})
            transcript = answer.get("transcript") or answer.get("answer_text") or ""
            if transcript:
                transcript_parts.append({
                    "question": question.get("question_text", ""),
                    "answer": transcript,
                    "score": answer.get("score")
                })

        # Generate AI analysis
        prompt = self._build_transcript_analysis_prompt(transcript_parts)

        try:
            response = await groq_service.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR professional. Analyze interview transcripts comprehensively."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            import json
            content = response.choices[0].message.content

            try:
                analysis = json.loads(content)
                return self._normalize_transcript_analysis(analysis)
            except json.JSONDecodeError:
                return self._fallback_transcript_analysis()

        except Exception as e:
            raise AIException(f"Failed to analyze transcript: {str(e)}")

    def _build_transcript_analysis_prompt(self, transcript_parts: List[Dict]) -> str:
        """Build prompt for transcript analysis.

        Args:
            transcript_parts: List of question-answer pairs

        Returns:
            Formatted prompt string
        """
        transcript_text = "\n\n".join([
            f"Q{i+1}: {part['question']}\nA: {part['answer']} (Score: {part.get('score', 'N/A')})"
            for i, part in enumerate(transcript_parts)
        ])

        return f"""Analyze this interview transcript and provide insights.

Transcript:
{transcript_text}

Return a JSON object with this exact format:
{{
    "overall_understanding_level": "excellent/good/fair/poor",
    "communication_clarity_score": 0-100,
    "technical_accuracy_score": 0-100,
    "consistency_score": 0-100,
    "areas_of_strength": ["strength1", "strength2"],
    "areas_for_improvement": ["area1", "area2"],
    "key_themes": ["theme1", "theme2"],
    "communication_style": "clear_and_concise/detailed_and_elaborate/vague_and_unclear",
    "recommended_next_steps": ["step1", "step2"]
}}

Return ONLY valid JSON, no other text."""

    def _normalize_transcript_analysis(self, analysis: Dict) -> Dict[str, Any]:
        """Normalize transcript analysis.

        Args:
            analysis: Raw analysis from AI

        Returns:
            Normalized analysis
        """
        return {
            "overall_understanding_level": analysis.get("overall_understanding_level", "fair"),
            "communication_clarity_score": max(0, min(100, analysis.get("communication_clarity_score", 50))),
            "technical_accuracy_score": max(0, min(100, analysis.get("technical_accuracy_score", 50))),
            "consistency_score": max(0, min(100, analysis.get("consistency_score", 50))),
            "areas_of_strength": analysis.get("areas_of_strength", []),
            "areas_for_improvement": analysis.get("areas_for_improvement", []),
            "key_themes": analysis.get("key_themes", []),
            "communication_style": analysis.get("communication_style", "detailed_and_elaborate"),
            "recommended_next_steps": analysis.get("recommended_next_steps", [])
        }

    def _fallback_transcript_analysis(self) -> Dict[str, Any]:
        """Return fallback transcript analysis.

        Returns:
            Default analysis
        """
        return {
            "overall_understanding_level": "fair",
            "communication_clarity_score": 50,
            "technical_accuracy_score": 50,
            "consistency_score": 50,
            "areas_of_strength": [],
            "areas_for_improvement": [],
            "key_themes": [],
            "communication_style": "detailed_and_elaborate",
            "recommended_next_steps": ["Review answers manually"]
        }

    async def save_evaluation(
        self,
        answer_id: str,
        evaluation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save evaluation results to database.

        Args:
            answer_id: Answer ID to update
            evaluation: Evaluation results

        Returns:
            Updated answer
        """
        update_data = {
            "score": evaluation.get("score"),
            "feedback": evaluation.get("feedback"),
            "technical_accuracy": evaluation.get("technical_accuracy"),
            "communication_clarity": evaluation.get("communication_clarity"),
            "concepts_detected": evaluation.get("concepts_detected", []),
            "concepts_missing": evaluation.get("concepts_missing", []),
            "strengths": evaluation.get("strengths", []),
            "improvements": evaluation.get("improvements", [])
        }

        response = await self.supabase.table("interview_answers").update(
            {k: v for k, v in update_data.items() if v is not None}
        ).eq("id", answer_id).execute()

        if not response.data:
            raise AIException("Failed to save evaluation")

        return response.data[0]


def create_evaluation_service(supabase_client: AsyncClient) -> EvaluationService:
    """Create an EvaluationService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured EvaluationService instance
    """
    return EvaluationService(supabase_client)
