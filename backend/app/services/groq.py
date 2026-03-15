from groq import AsyncGroq
from app.config import settings
from app.exceptions import AIException
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class DifficultyLevel(str, Enum):
    """Question difficulty levels for progressive interviewing."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class QuestionCategory(str, Enum):
    """Categories of interview questions."""
    CONCEPT = "concept"           # Theory and definitions
    PRACTICAL = "practical"       # Code/implementation
    REAL_WORLD = "real_world"    # Scenario-based
    PROBLEM_SOLVING = "problem_solving"
    BEHAVIORAL = "behavioral"


class AnswerQuality(str, Enum):
    """Quality assessment for answers."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    WEAK = "weak"
    POOR = "poor"


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

    # =========================================================================
    # AI INTERVIEW BEHAVIOR ENGINE - PHASE 3
    # =========================================================================

    async def generate_progressive_questions(
        self,
        skill: str,
        job_title: str,
        candidate_level: str = "intermediate",
        count_per_level: int = 2
    ) -> Dict[str, List[Dict]]:
        """Generate progressive questions across difficulty levels.

        Questions progress from:
        1. CONCEPT - Basic theory and definitions
        2. PRACTICAL - Implementation and code
        3. REAL_WORLD - Application and scenarios

        Args:
            skill: The skill to generate questions for
            job_title: Job title for context
            candidate_level: Expected candidate level (beginner/intermediate/advanced/expert)
            count_per_level: Number of questions per difficulty level

        Returns:
            Dictionary with question arrays for each level:
            {
                "beginner": [{"question": "...", "category": "concept", ...}],
                "intermediate": [...],
                "advanced": [...]
            }
        """
        level_difficulty_map = {
            "beginner": "basic definitions, fundamental concepts",
            "intermediate": "practical applications, common use cases",
            "advanced": "edge cases, optimization, advanced patterns",
            "expert": "system design, architectural decisions, trade-offs"
        }

        prompt = f"""Generate {count_per_level} questions for a {skill} skill at a {candidate_level} level for a {job_title} position.

For each difficulty level, create questions that progress from theory to practice:
- CONCEPT: Basic definitions, "what is", "how does X work"
- PRACTICAL: Implementation, code, "how would you implement"
- REAL_WORLD: Scenarios, trade-offs, "describe a time when"

Return a JSON object with this structure:
{{
    "questions": [
        {{
            "question": "question text",
            "skill": "{skill}",
            "category": "concept/practical/real_world",
            "difficulty": "beginner/intermediate/advanced/expert",
            "expected_concepts": ["concept1", "concept2"],
            "sample_good_answer": "key points a good answer should contain"
        }}
    ]
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer. Create progressive questions that test deep understanding."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2500
            )

            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                return result.get("questions", [])
            except json.JSONDecodeError:
                return []
        except Exception as e:
            raise AIException(f"Failed to generate progressive questions: {str(e)}")

    async def generate_follow_up_question(
        self,
        original_question: str,
        candidate_answer: str,
        answer_evaluation: Dict[str, Any],
        skill: str
    ) -> Optional[Dict]:
        """Generate adaptive follow-up questions based on answer quality.

        Follow-up logic:
        - WEAK/POOR answer → Ask simpler clarifying question
        - ADEQUATE → Probe deeper into the same topic
        - GOOD/EXCELLENT → Ask about edge cases or next-level concepts

        Args:
            original_question: The question that was answered
            candidate_answer: The candidate's response
            answer_evaluation: Previous evaluation of the answer
            skill: The skill being tested

        Returns:
            Follow-up question object or None if not needed
        """
        quality = answer_evaluation.get("quality", "adequate")
        score = answer_evaluation.get("score", 50)

        # Determine follow-up type based on answer quality
        if score >= 85:
            follow_up_type = "advance"
            instruction = "Ask about edge cases, optimization, or trade-offs to test deeper understanding."
        elif score >= 70:
            follow_up_type = "deepen"
            instruction = "Probe deeper into the topic to explore nuances or practical applications."
        elif score >= 50:
            follow_up_type = "clarify"
            instruction = "Ask a clarifying question to better understand their knowledge gaps."
        else:
            follow_up_type = "simplify"
            instruction = "Ask a simpler foundational question to establish baseline knowledge."

        prompt = f"""Generate an adaptive follow-up question based on the candidate's answer.

Original Question: {original_question}
Candidate's Answer: {candidate_answer}
Answer Score: {score}/100
Answer Quality: {quality}
Follow-up Type: {follow_up_type}
Instruction: {instruction}

Generate a follow-up question that:
1. Builds on their answer (if adequate or better)
2. Addresses gaps (if weak)
3. Tests deeper understanding (if excellent)

Return a JSON object:
{{
    "follow_up_question": "the follow-up question text",
    "follow_up_type": "advance/deepen/clarify/simplify",
    "reasoning": "why this follow-up is appropriate",
    "expected_concepts": ["concepts the candidate should demonstrate"],
    "difficulty_adjustment": "easier/same/harder"
}}

Return ONLY valid JSON, no other text. If no follow-up is needed, return {{"follow_up_question": null}}."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer. Generate intelligent follow-up questions that probe candidate understanding."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=800
            )

            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                if result.get("follow_up_question"):
                    return {
                        "question": result["follow_up_question"],
                        "type": result.get("follow_up_type", "deepen"),
                        "reasoning": result.get("reasoning", ""),
                        "expected_concepts": result.get("expected_concepts", []),
                        "difficulty_adjustment": result.get("difficulty_adjustment", "same")
                    }
                return None
            except json.JSONDecodeError:
                return None
        except Exception as e:
            raise AIException(f"Failed to generate follow-up: {str(e)}")

    async def evaluate_answer_detailed(
        self,
        question: Dict[str, Any],
        answer: str,
        audio_transcript: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform multi-dimensional answer evaluation with concept detection.

        Evaluation dimensions:
        1. Technical Accuracy - Correctness of technical content
        2. Depth of Understanding - Shows genuine comprehension
        3. Communication - Clarity of expression
        4. Practical Application - Can apply concepts to real scenarios
        5. Completeness - Addresses all parts of the question

        Also detects:
        - Concepts correctly demonstrated
        - Concepts missing or incorrect
        - Key terms used

        Args:
            question: The question object with metadata
            answer: The candidate's text answer
            audio_transcript: Optional transcript if answer was audio

        Returns:
            Comprehensive evaluation object with scores and detected concepts
        """
        question_text = question.get("question", "")
        skill = question.get("skill", "general")
        expected_concepts = question.get("expected_concepts", [])
        category = question.get("category", "practical")

        text_to_evaluate = answer
        if audio_transcript:
            text_to_evaluate = f"Text Answer: {answer}\n\nAudio Transcript: {audio_transcript}"

        prompt = f"""Evaluate this interview answer across multiple dimensions.

Question: {question_text}
Skill Tested: {skill}
Category: {category}
Expected Concepts: {", ".join(expected_concepts) if expected_concepts else "none specified"}

Candidate's Answer:
{text_to_evaluate}

Return a detailed JSON evaluation:
{{
    "quality": "excellent/good/adequate/weak/poor",
    "overall_score": 0-100,
    "dimensions": {{
        "technical_accuracy": 0-100,
        "depth_of_understanding": 0-100,
        "communication_clarity": 0-100,
        "practical_application": 0-100,
        "completeness": 0-100
    }},
    "detected_concepts": ["concept1", "concept2"],
    "missing_concepts": ["concept1", "concept2"],
    "incorrect_concepts": ["any wrongly mentioned concepts"],
    "key_terms_used": ["technical terms the candidate used correctly"],
    "feedback": "constructive feedback on the answer",
    "strengths": ["specific strength1", "specific strength2"],
    "areas_for_improvement": ["specific area1", "specific area2"],
    "suggested_follow_up": "type of follow-up that would help (clarify/deepen/advance)"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer. Provide detailed, constructive multi-dimensional evaluations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            try:
                evaluation = json.loads(content)
                # Normalize quality string
                quality_map = {
                    "excellent": AnswerQuality.EXCELLENT,
                    "good": AnswerQuality.GOOD,
                    "adequate": AnswerQuality.ADEQUATE,
                    "weak": AnswerQuality.WEAK,
                    "poor": AnswerQuality.POOR
                }
                evaluation["quality"] = quality_map.get(
                    evaluation.get("quality", "adequate").lower(),
                    AnswerQuality.ADEQUATE
                )
                return evaluation
            except json.JSONDecodeError:
                return self._default_evaluation()
        except Exception as e:
            raise AIException(f"Failed to evaluate answer: {str(e)}")

    def _default_evaluation(self) -> Dict[str, Any]:
        """Return a default evaluation structure."""
        return {
            "quality": AnswerQuality.ADEQUATE,
            "overall_score": 50,
            "dimensions": {
                "technical_accuracy": 50,
                "depth_of_understanding": 50,
                "communication_clarity": 50,
                "practical_application": 50,
                "completeness": 50
            },
            "detected_concepts": [],
            "missing_concepts": [],
            "incorrect_concepts": [],
            "key_terms_used": [],
            "feedback": "Unable to evaluate answer",
            "strengths": [],
            "areas_for_improvement": [],
            "suggested_follow_up": "clarify"
        }

    async def aggregate_skill_scores(
        self,
        skill_evaluations: List[Dict[str, Any]],
        skills_tested: List[str]
    ) -> Dict[str, Any]:
        """Aggregate scores across all answers to generate skill-level scores.

        Args:
            skill_evaluations: List of detailed evaluations from evaluate_answer_detailed
            skills_tested: List of skills that were tested

        Returns:
            Aggregated skill scores with statistics
        """
        if not skill_evaluations:
            return {
                "skills": {},
                "overall_score": 0,
                "total_questions": 0,
                "summary": "No evaluations to aggregate"
            }

        # Group evaluations by skill
        skill_groups: Dict[str, List[Dict]] = {}
        for eval_item in skill_evaluations:
            skill = eval_item.get("skill", "general")
            if skill not in skill_groups:
                skill_groups[skill] = []
            skill_groups[skill].append(eval_item)

        # Calculate aggregated scores per skill
        skill_scores = {}
        for skill, evaluations in skill_groups.items():
            scores = [e.get("overall_score", 0) for e in evaluations]
            dimension_scores = {
                dim: sum(e.get("dimensions", {}).get(dim, 0) for e in evaluations) / len(evaluations)
                for dim in ["technical_accuracy", "depth_of_understanding",
                           "communication_clarity", "practical_application", "completeness"]
            }

            skill_scores[skill] = {
                "average_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
                "question_count": len(scores),
                "dimensions": dimension_scores,
                "consistent": max(scores) - min(scores) < 20  # Low variance = consistent
            }

        # Calculate overall score
        all_scores = [e.get("overall_score", 0) for e in skill_evaluations]
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0

        return {
            "skills": skill_scores,
            "overall_score": round(overall_score, 2),
            "total_questions": len(skill_evaluations),
            "average_consistency": sum(
                1 for s in skill_scores.values() if s.get("consistent", False)
            ) / len(skill_scores) if skill_scores else 0,
            "strongest_skill": max(skill_scores.items(), key=lambda x: x[1]["average_score"])[0]
                if skill_scores else None,
            "weakest_skill": min(skill_scores.items(), key=lambda x: x[1]["average_score"])[0]
                if skill_scores else None
        }

    async def generate_interview_report(
        self,
        candidate_name: str,
        job_title: str,
        skill_evaluations: List[Dict[str, Any]],
        skill_aggregates: Dict[str, Any],
        interview_duration_minutes: int,
        candidate_strengths: List[str] = None,
        candidate_weaknesses: List[str] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive structured interview report.

        Report includes:
        1. Executive Summary
        2. Skill-by-Skill Breakdown
        3. Dimension Analysis
        4. Behavioral Observations
        5. Strengths & Areas for Growth
        6. Recommendation with Justification

        Args:
            candidate_name: Candidate's name or identifier
            job_title: Position being interviewed for
            skill_evaluations: Individual answer evaluations
            skill_aggregates: Aggregated skill scores
            interview_duration_minutes: Total interview duration
            candidate_strengths: Pre-identified strengths
            candidate_weaknesses: Pre-identified weaknesses

        Returns:
            Structured report dictionary
        """
        # Prepare summary data
        total_questions = len(skill_evaluations)
        overall_score = skill_aggregates.get("overall_score", 0)

        # Determine recommendation
        if overall_score >= 80:
            recommendation = "strong_hire"
            recommendation_reason = "Exceptional performance across most skill areas"
        elif overall_score >= 70:
            recommendation = "hire"
            recommendation_reason = "Solid performance meets job requirements"
        elif overall_score >= 60:
            recommendation = "conditional_hire"
            recommendation_reason = "Adequate skills with some areas for development"
        elif overall_score >= 50:
            recommendation = "no_hire"
            recommendation_reason = "Below minimum threshold for this role"
        else:
            recommendation = "no_hire"
            recommendation_reason = "Significant skill gaps identified"

        prompt = f"""Generate a comprehensive interview report for a {job_title} candidate.

Candidate: {candidate_name}
Interview Duration: {interview_duration_minutes} minutes
Total Questions Asked: {total_questions}
Overall Score: {overall_score}/100

Skill Performance Summary:
{json.dumps(skill_aggregates.get("skills", {}), indent=2)}

Individual Evaluations:
{json.dumps(skill_evaluations[:5], indent=2)}  # First 5 for context

Generate a detailed report with:

1. EXECUTIVE SUMMARY
   - Overall impression
   - Key finding
   - Recommendation

2. SKILL BREAKDOWN
   - Score per skill
   - Performance trend (improving/declining/stable)

3. DIMENSION ANALYSIS
   - Technical Accuracy score
   - Communication score
   - Problem Solving score
   - Practical Application score

4. STRENGTHS (3-5 specific)
   - Skills demonstrated well
   - Key positive behaviors

5. AREAS FOR DEVELOPMENT (3-5 specific)
   - Skill gaps
   - Recommended training

6. INTERVIEW BEHAVIOR INSIGHTS
   - Engagement level
   - Confidence indicators
   - Communication style

7. FINAL RECOMMENDATION
   - hire/conditional_hire/no_hire/strong_hire
   - justification
   - next steps

Return ONLY valid JSON:
{{
    "report_id": "unique_report_id",
    "generated_at": "ISO timestamp",
    "candidate_name": "{candidate_name}",
    "job_title": "{job_title}",
    "interview_duration_minutes": {interview_duration_minutes},
    "total_questions": {total_questions},
    "executive_summary": {{
        "overall_score": {overall_score},
        "overall_impression": "summary text",
        "key_finding": "key insight"
    }},
    "skill_breakdown": [
        {{
            "skill": "skill name",
            "score": 0-100,
            "question_count": 0,
            "performance_trend": "improving/declining/stable",
            "notes": "specific observations"
        }}
    ],
    "dimension_scores": {{
        "technical_accuracy": 0-100,
        "communication_clarity": 0-100,
        "problem_solving": 0-100,
        "practical_application": 0-100,
        "completeness": 0-100
    }},
    "strengths": ["strength1", "strength2"],
    "areas_for_development": ["area1", "area2"],
    "behavioral_insights": {{
        "engagement": "high/medium/low",
        "confidence": "high/medium/low",
        "communication_style": "clear/mixed/unclear"
    }},
    "recommendation": {{
        "decision": "strong_hire/hire/conditional_hire/no_hire",
        "confidence": 0-100,
        "justification": "reasoning",
        "next_steps": ["suggested action1"]
    }}
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert HR professional. Generate comprehensive, fair interview reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2500
            )

            content = response.choices[0].message.content
            try:
                report = json.loads(content)
                report["generated_at"] = report.get("generated_at", "2024-01-01T00:00:00Z")
                report["report_id"] = f"rpt_{candidate_name}_{job_title}_{int(overall_score)}"
                return report
            except json.JSONDecodeError:
                return self._default_report(candidate_name, job_title, overall_score, total_questions)
        except Exception as e:
            raise AIException(f"Failed to generate report: {str(e)}")

    def _default_report(
        self,
        candidate_name: str,
        job_title: str,
        overall_score: float,
        total_questions: int
    ) -> Dict[str, Any]:
        """Generate a default report structure if AI generation fails."""
        return {
            "report_id": f"rpt_{candidate_name}_{job_title}_{int(overall_score)}",
            "generated_at": "2024-01-01T00:00:00Z",
            "candidate_name": candidate_name,
            "job_title": job_title,
            "interview_duration_minutes": 0,
            "total_questions": total_questions,
            "executive_summary": {
                "overall_score": overall_score,
                "overall_impression": "Interview completed",
                "key_finding": f"Scored {overall_score}/100"
            },
            "skill_breakdown": [],
            "dimension_scores": {
                "technical_accuracy": overall_score,
                "communication_clarity": overall_score,
                "problem_solving": overall_score,
                "practical_application": overall_score,
                "completeness": overall_score
            },
            "strengths": [],
            "areas_for_development": [],
            "behavioral_insights": {
                "engagement": "medium",
                "confidence": "medium",
                "communication_style": "clear"
            },
            "recommendation": {
                "decision": "conditional_hire" if overall_score >= 50 else "no_hire",
                "confidence": 50,
                "justification": "Report generation had issues",
                "next_steps": ["Review raw evaluation data"]
            }
        }


# Singleton instance
groq_service = GroqService()
