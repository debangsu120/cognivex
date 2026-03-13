from groq import AsyncGroq
from app.config import settings
from app.exceptions import AIException
from typing import List, Dict, Optional
import json


class GroqService:
    """Service for AI operations using Groq."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def extract_resume_details(self, resume_text: str) -> Dict:
        """Extract detailed information from resume using AI.

        Args:
            resume_text: Raw resume text content

        Returns:
            Dictionary containing:
                - skills: List of extracted skills
                - years_of_experience: Estimated years of experience
                - education: Education details
                - technologies: List of technologies/tools
        """
        prompt = f"""Analyze the following resume and extract:
1. skills: ["Python", "JavaScript", ...] - technical and soft skills
2. years_of_experience: number - estimated total years
3. education: "B.Tech in Computer Science" - education details
4. technologies: ["AWS", "Docker", "React", ...] - specific technologies/tools

Resume text:
{resume_text}

Return JSON only with this exact format:
{{
    "skills": [],
    "years_of_experience": 0,
    "education": "",
    "technologies": []
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a resume parser. Extract detailed information from resumes. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            try:
                details = json.loads(content)
                return {
                    "skills": details.get("skills", []),
                    "years_of_experience": details.get("years_of_experience", 0),
                    "education": details.get("education", ""),
                    "technologies": details.get("technologies", [])
                }
            except json.JSONDecodeError:
                return {
                    "skills": [],
                    "years_of_experience": 0,
                    "education": "",
                    "technologies": []
                }
        except Exception as e:
            raise AIException(f"Failed to extract resume details: {str(e)}")

    async def generate_interview_questions_enhanced(
        self,
        job_title: str,
        job_description: str,
        skills_required: List[str],
        difficulty: str = "medium",
        count: int = 5
    ) -> List[Dict]:
        """Generate enhanced interview questions with skill linkage.

        Args:
            job_title: Job title
            job_description: Job description
            skills_required: List of required skills
            difficulty: Question difficulty (easy/medium/hard)
            count: Number of questions to generate

        Returns:
            List of questions with skill, category, and difficulty
        """
        skills_str = ", ".join(skills_required) if skills_required else "general"

        prompt = f"""Generate {count} interview questions for a {job_title} position.
Job Description: {job_description}
Required Skills: {skills_str}
Difficulty Level: {difficulty}

For each question include:
- question: The question text
- skill: The skill this question tests (one of the required skills)
- category: concept/application/advanced (what type of question)
- difficulty: easy/medium/hard

Return a JSON array of objects with this format:
[{{
    "question": "question text",
    "skill": "Python",
    "category": "concept/application/advanced",
    "difficulty": "easy/medium/hard"
}}]

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert HR professional. Generate relevant interview questions linked to specific skills."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            try:
                questions = json.loads(content)
                if isinstance(questions, list):
                    # Validate and normalize each question
                    normalized = []
                    for q in questions:
                        normalized.append({
                            "question": q.get("question", ""),
                            "skill": q.get("skill", skills_required[0] if skills_required else "general"),
                            "category": q.get("category", "application"),
                            "difficulty": q.get("difficulty", difficulty)
                        })
                    return normalized
                return []
            except json.JSONDecodeError:
                return []
        except Exception as e:
            raise AIException(f"Failed to generate enhanced questions: {str(e)}")

    async def extract_skills_from_resume(self, resume_text: str) -> List[str]:
        """Extract skills from resume text using AI.

        Args:
            resume_text: Raw resume text content

        Returns:
            List of extracted skill names
        """
        # Use the enhanced method and extract just skills
        details = await self.extract_resume_details(resume_text)
        return details.get("skills", [])

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
