"""
Embedding Service for Vector-Based Skill Matching

Provides semantic matching between candidate skills and job requirements
using embedding similarity calculations.
"""

from typing import List, Dict, Optional, Any
import hashlib
import json
from supabase import AsyncClient

from app.config import settings
from app.exceptions import AIException


class EmbeddingService:
    """Service for generating and managing skill embeddings."""

    def __init__(self, supabase_client: AsyncClient):
        self.supabase = supabase_client
        self.embedding_model = "multilingual-e5-large"

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using Groq.

        Args:
            text: Text to embed (skill name, job requirement, etc.)

        Returns:
            Embedding vector as list of floats
        """
        try:
            # Import Groq client
            from groq import AsyncGroq
            client = AsyncGroq(api_key=settings.groq_api_key)

            response = await client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            return response.data[0].embedding
        except Exception as e:
            raise AIException(f"Failed to generate embedding: {str(e)}")

    async def store_embedding(
        self,
        skill_name: str,
        category: Optional[str] = None,
        related_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate and store embedding for a skill.

        Args:
            skill_name: Name of the skill
            category: Category (e.g., "programming", "framework")
            related_skills: List of related skill names

        Returns:
            Stored embedding record
        """
        # Check if already exists
        existing = await self.supabase.table("skill_embeddings").select(
            "id"
        ).eq("skill_name", skill_name.lower()).execute()

        if existing.data:
            return {"id": existing.data[0]["id"], "status": "exists"}

        # Generate embedding
        embedding = await self.generate_embedding(skill_name)

        # Store
        data = {
            "skill_name": skill_name.lower(),
            "embedding": json.dumps(embedding),
            "category": category,
            "related_skills": related_skills or []
        }

        result = await self.supabase.table("skill_embeddings").insert(data).execute()

        return result.data[0] if result.data else {"status": "error"}

    async def find_similar_skills(
        self,
        skill: str,
        threshold: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find skills similar to the given skill using cosine similarity.

        Args:
            skill: Skill name to match
            threshold: Minimum similarity score (0-1)
            limit: Maximum results to return

        Returns:
            List of similar skills with similarity scores
        """
        # Generate embedding for the input skill
        query_embedding = await self.generate_embedding(skill)

        # Get all stored embeddings
        result = await self.supabase.table("skill_embeddings").select("*").execute()

        if not result.data:
            return []

        # Calculate cosine similarity for each
        similarities = []
        for row in result.data:
            stored_embedding = json.loads(row["embedding"])
            similarity = self._cosine_similarity(query_embedding, stored_embedding)

            if similarity >= threshold:
                similarities.append({
                    "skill_name": row["skill_name"],
                    "category": row["category"],
                    "similarity": round(similarity, 3),
                    "related_skills": row.get("related_skills", [])
                })

        # Sort by similarity descending
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return similarities[:limit]

    async def match_candidate_skills_to_job(
        self,
        candidate_skills: List[str],
        job_skills: List[str]
    ) -> Dict[str, Any]:
        """Match candidate skills to job requirements using semantic similarity.

        Args:
            candidate_skills: List of skills from candidate profile
            job_skills: List of required skills for the job

        Returns:
            Matching results with scores
        """
        matches = []
        unmatched_candidate = []
        matched_job_skills = set()

        for candidate_skill in candidate_skills:
            best_match = None
            best_score = 0

            for job_skill in job_skills:
                # Check exact match first
                if candidate_skill.lower() == job_skill.lower():
                    best_match = {
                        "skill": job_skill,
                        "match_type": "exact",
                        "score": 1.0
                    }
                    best_score = 1.0
                    break

                # Semantic similarity
                similarity = await self._compute_similarity(
                    candidate_skill,
                    job_skill
                )

                if similarity > best_score:
                    best_score = similarity
                    best_match = {
                        "skill": job_skill,
                        "match_type": "semantic" if similarity < 1.0 else "exact",
                        "score": similarity
                    }

            if best_match and best_score >= 0.6:
                matches.append({
                    "candidate_skill": candidate_skill,
                    "matched_skill": best_match["skill"],
                    "match_type": best_match["match_type"],
                    "score": round(best_match["score"], 3)
                })
                matched_job_skills.add(best_match["skill"])
            else:
                unmatched_candidate.append(candidate_skill)

        # Calculate match score
        match_percentage = (
            len(matched_job_skills) / len(job_skills) * 100
            if job_skills else 0
        )

        return {
            "matched_skills": matches,
            "unmatched_candidate_skills": unmatched_candidate,
            "unmatched_job_skills": [s for s in job_skills if s not in matched_job_skills],
            "match_score": round(match_percentage, 1),
            "total_required": len(job_skills),
            "total_matched": len(matched_job_skills)
        }

    async def _compute_similarity(self, skill1: str, skill2: str) -> float:
        """Compute semantic similarity between two skills.

        Args:
            skill1: First skill name
            skill2: Second skill name

        Returns:
            Similarity score (0-1)
        """
        try:
            embedding1 = await self.generate_embedding(skill1)
            embedding2 = await self.generate_embedding(skill2)
            return self._cosine_similarity(embedding1, embedding2)
        except Exception:
            return 0.0

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        if not vec1 or not vec2:
            return 0.0

        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def get_or_create_skill_embedding(
        self,
        skill_name: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing embedding or create new one.

        Args:
            skill_name: Name of the skill
            category: Optional category

        Returns:
            Embedding record
        """
        # Try to get existing
        result = await self.supabase.table("skill_embeddings").select(
            "*"
        ).eq("skill_name", skill_name.lower()).execute()

        if result.data:
            return result.data[0]

        # Create new
        return await self.store_embedding(skill_name, category)

    async def batch_store_embeddings(
        self,
        skills: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Store embeddings for multiple skills.

        Args:
            skills: List of dicts with 'name' and optional 'category'

        Returns:
            Summary of stored embeddings
        """
        stored = 0
        skipped = 0
        errors = []

        for skill in skills:
            try:
                result = await self.store_embedding(
                    skill_name=skill["name"],
                    category=skill.get("category")
                )
                if result.get("status") == "exists":
                    skipped += 1
                else:
                    stored += 1
            except Exception as e:
                errors.append({"skill": skill["name"], "error": str(e)})

        return {
            "stored": stored,
            "skipped": skipped,
            "errors": errors
        }


def create_embedding_service(supabase_client: AsyncClient) -> EmbeddingService:
    """Create an EmbeddingService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured EmbeddingService
    """
    return EmbeddingService(supabase_client)
