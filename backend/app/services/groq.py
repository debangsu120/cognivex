from groq import AsyncGroq
from app.config import settings
from app.exceptions import AIException
from typing import List, Dict, Optional
import json


class GroqService:
    """Service for AI operations using Groq."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def extract_skills_from_resume(self, resume_text: str) -> List[str]:
        """Extract skills from resume text using AI."""
        prompt = f"""Analyze the following resume text and extract all technical skills, soft skills, and professional competencies.
Return only a JSON array of skill names, nothing else.

Resume text:
{resume_text}

Return a JSON array like: ["Python", "JavaScript", "Project Management", "AWS"]"""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a resume parser. Extract skills from resumes. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            content = response.choices[0].message.content
            # Try to parse JSON from the response
            try:
                skills = json.loads(content)
                if isinstance(skills, list):
                    return skills
            except json.JSONDecodeError:
                # Try to extract array from text
                import re
                match = re.search(r'\[(.*?)\]', content)
                if match:
                    skills_str = match.group(1)
                    return [s.strip().strip('"').strip("'") for s in skills_str.split(",")]

            return []
        except Exception as e:
            raise AIException(f"Failed to extract skills: {str(e)}")

    async def generate_interview_questions(
        self,
        job_title: str,
        job_description: str,
        skills_required: List[str],
        difficulty: str = "medium",
        count: int = 5
    ) -> List[Dict]:
        """Generate interview questions based on job requirements."""
        skills_str = ", ".join(skills_required) if skills_required else "general"

        prompt = f"""Generate {count} interview questions for a {job_title} position.
Job Description: {job_description}
Required Skills: {skills_str}
Difficulty Level: {difficulty}

Return a JSON array of objects with this format:
[{{"question": "question text", "category": "category name", "difficulty": "easy/medium/hard"}}]

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert HR professional. Generate relevant interview questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            try:
                questions = json.loads(content)
                return questions if isinstance(questions, list) else []
            except json.JSONDecodeError:
                return []
        except Exception as e:
            raise AIException(f"Failed to generate questions: {str(e)}")

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        skills_required: List[str]
    ) -> Dict:
        """Evaluate a candidate's answer to an interview question."""
        skills_str = ", ".join(skills_required) if skills_required else "general"

        prompt = f"""Evaluate the following interview answer and provide a score and feedback.

Question: {question}

Candidate's Answer: {answer}

Required Skills for this question: {skills_str}

Return a JSON object with this exact format:
{{
    "score": 0-100,
    "technical_accuracy": 0-100,
    "communication_clarity": 0-100,
    "feedback": "constructive feedback",
    "strengths": ["strength1", "strength2"],
    "areas_for_improvement": ["area1", "area2"]
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer. Provide fair and constructive evaluation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            content = response.choices[0].message.content
            try:
                evaluation = json.loads(content)
                return evaluation
            except json.JSONDecodeError:
                return {
                    "score": 50,
                    "technical_accuracy": 50,
                    "communication_clarity": 50,
                    "feedback": "Unable to evaluate answer",
                    "strengths": [],
                    "areas_for_improvement": []
                }
        except Exception as e:
            raise AIException(f"Failed to evaluate answer: {str(e)}")

    async def generate_overall_feedback(
        self,
        interview_answers: List[Dict],
        job_title: str
    ) -> Dict:
        """Generate overall interview feedback based on all answers."""
        answers_summary = "\n".join([
            f"Q{i+1}: {a.get('question', 'N/A')}\nA: {a.get('answer', 'N/A')}\nScore: {a.get('score', 'N/A')}"
            for i, a in enumerate(interview_answers)
        ])

        prompt = f"""Provide overall interview feedback for a {job_title} candidate based on their answers.

Interview Answers:
{answers_summary}

Return a JSON object with this exact format:
{{
    "overall_score": 0-100,
    "technical_score": 0-100,
    "communication_score": 0-100,
    "problem_solving_score": 0-100,
    "cultural_fit_score": 0-100,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "summary": "overall summary paragraph",
    "recommendation": "hire/no_hire/uncertain"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert HR professional. Provide comprehensive interview feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            try:
                feedback = json.loads(content)
                return feedback
            except json.JSONDecodeError:
                return {
                    "overall_score": 50,
                    "technical_score": 50,
                    "communication_score": 50,
                    "problem_solving_score": 50,
                    "cultural_fit_score": 50,
                    "strengths": [],
                    "weaknesses": [],
                    "summary": "Unable to generate feedback",
                    "recommendation": "uncertain"
                }
        except Exception as e:
            raise AIException(f"Failed to generate feedback: {str(e)}")

    async def match_candidate_to_job(
        self,
        candidate_skills: List[str],
        candidate_experience_years: int,
        job_title: str,
        job_requirements: List[str],
        job_skills_required: List[str]
    ) -> Dict:
        """Match a candidate to a job based on skills and experience."""
        candidate_skills_str = ", ".join(candidate_skills) if candidate_skills else "none"
        job_skills_str = ", ".join(job_skills_required) if job_skills_required else "general"

        prompt = f"""Analyze the candidate-job fit and provide a detailed matching analysis.

Candidate Profile:
- Skills: {candidate_skills_str}
- Experience: {candidate_experience_years} years

Job Requirements:
- Title: {job_title}
- Requirements: {", ".join(job_requirements) if job_requirements else "none specified"}
- Required Skills: {job_skills_str}

Return a JSON object with this exact format:
{{
    "skills_match_score": 0-100,
    "experience_match_score": 0-100,
    "overall_match_score": 0-100,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "recommendation": "strong_match/good_match/poor_match"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert recruiter. Analyze candidate-job fit accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )

            content = response.choices[0].message.content
            try:
                match_result = json.loads(content)
                return match_result
            except json.JSONDecodeError:
                return {
                    "skills_match_score": 50,
                    "experience_match_score": 50,
                    "overall_match_score": 50,
                    "matched_skills": [],
                    "missing_skills": [],
                    "recommendation": "uncertain"
                }
        except Exception as e:
            raise AIException(f"Failed to match candidate: {str(e)}")


# Singleton instance
groq_service = GroqService()
