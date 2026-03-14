from supabase import create_client, Client
from app.config import settings
from typing import Optional, Any, Dict, List


class SupabaseService:
    """Service for interacting with Supabase."""

    def __init__(self):
        self.url = settings.supabase_url
        self.key = settings.supabase_key
        self.service_key = settings.supabase_service_key
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client

    @property
    def service_client(self) -> Client:
        """Admin client with service role key."""
        return create_client(self.url, self.service_key)

    # Profile operations
    async def get_profile(self, user_id: str) -> Optional[Dict]:
        response = self.client.table("profiles").select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None

    async def create_profile(self, profile_data: Dict) -> Dict:
        response = self.client.table("profiles").insert(profile_data).execute()
        return response.data[0]

    async def update_profile(self, user_id: str, profile_data: Dict) -> Dict:
        response = self.client.table("profiles").update(profile_data).eq("user_id", user_id).execute()
        return response.data[0]

    # Company operations
    async def get_company(self, company_id: str) -> Optional[Dict]:
        response = self.client.table("companies").select("*").eq("id", company_id).execute()
        return response.data[0] if response.data else None

    async def create_company(self, company_data: Dict) -> Dict:
        response = self.client.table("companies").insert(company_data).execute()
        return response.data[0]

    async def update_company(self, company_id: str, company_data: Dict) -> Dict:
        response = self.client.table("companies").update(company_data).eq("id", company_id).execute()
        return response.data[0]

    async def list_companies(self, owner_id: str) -> List[Dict]:
        response = self.client.table("companies").select("*").eq("owner_id", owner_id).execute()
        return response.data

    # Job operations
    async def get_job(self, job_id: str) -> Optional[Dict]:
        response = self.client.table("jobs").select("*, companies(*)").eq("id", job_id).execute()
        return response.data[0] if response.data else None

    async def create_job(self, job_data: Dict) -> Dict:
        response = self.client.table("jobs").insert(job_data).execute()
        return response.data[0]

    async def update_job(self, job_id: str, job_data: Dict) -> Dict:
        response = self.client.table("jobs").update(job_data).eq("id", job_id).execute()
        return response.data[0]

    async def list_jobs(self, company_id: Optional[str] = None, is_active: bool = True) -> List[Dict]:
        query = self.client.table("jobs").select("*, companies(*)")
        if company_id:
            query = query.eq("company_id", company_id)
        if is_active is not None:
            query = query.eq("is_active", is_active)
        response = query.execute()
        return response.data

    async def delete_job(self, job_id: str) -> bool:
        response = self.client.table("jobs").delete().eq("id", job_id).execute()
        return len(response.data) > 0

    # Resume operations
    async def get_resume(self, resume_id: str) -> Optional[Dict]:
        response = self.client.table("resumes").select("*").eq("id", resume_id).execute()
        return response.data[0] if response.data else None

    async def get_user_resumes(self, user_id: str) -> List[Dict]:
        response = self.client.table("resumes").select("*").eq("user_id", user_id).execute()
        return response.data

    async def create_resume(self, resume_data: Dict) -> Dict:
        response = self.client.table("resumes").insert(resume_data).execute()
        return response.data[0]

    async def update_resume(self, resume_id: str, resume_data: Dict) -> Dict:
        response = self.client.table("resumes").update(resume_data).eq("id", resume_id).execute()
        return response.data[0]

    # Interview operations
    async def get_interview(self, interview_id: str) -> Optional[Dict]:
        response = self.client.table("interviews").select("*, jobs(*), profiles!interviews_candidate_id_fkey(*)").eq("id", interview_id).execute()
        return response.data[0] if response.data else None

    async def create_interview(self, interview_data: Dict) -> Dict:
        response = self.client.table("interviews").insert(interview_data).execute()
        return response.data[0]

    async def update_interview(self, interview_id: str, interview_data: Dict) -> Dict:
        response = self.client.table("interviews").update(interview_data).eq("id", interview_id).execute()
        return response.data[0]

    async def list_interviews(self, candidate_id: Optional[str] = None, job_id: Optional[str] = None) -> List[Dict]:
        query = self.client.table("interviews").select("*, jobs(*)")
        if candidate_id:
            query = query.eq("candidate_id", candidate_id)
        if job_id:
            query = query.eq("job_id", job_id)
        response = query.execute()
        return response.data

    # Interview Questions
    async def create_question(self, question_data: Dict) -> Dict:
        response = self.client.table("interview_questions").insert(question_data).execute()
        return response.data[0]

    async def get_interview_questions(self, interview_id: str) -> List[Dict]:
        response = self.client.table("interview_questions").select("*").eq("interview_id", interview_id).order("question_order").execute()
        return response.data

    # Interview Answers
    async def create_answer(self, answer_data: Dict) -> Dict:
        response = self.client.table("interview_answers").insert(answer_data).execute()
        return response.data[0]

    async def update_answer(self, answer_id: str, answer_data: Dict) -> Dict:
        response = self.client.table("interview_answers").update(answer_data).eq("id", answer_id).execute()
        return response.data[0]

    async def get_question_answer(self, question_id: str) -> Optional[Dict]:
        response = self.client.table("interview_answers").select("*").eq("question_id", question_id).execute()
        return response.data[0] if response.data else None

    # Interview Scores
    async def create_score(self, score_data: Dict) -> Dict:
        response = self.client.table("interview_scores").insert(score_data).execute()
        return response.data[0]

    async def update_score(self, interview_id: str, score_data: Dict) -> Dict:
        response = self.client.table("interview_scores").update(score_data).eq("interview_id", interview_id).execute()
        return response.data[0]

    async def get_interview_score(self, interview_id: str) -> Optional[Dict]:
        response = self.client.table("interview_scores").select("*").eq("interview_id", interview_id).execute()
        return response.data[0] if response.data else None

    # Skills operations
    async def get_all_skills(self) -> List[Dict]:
        response = self.client.table("skills").select("*").execute()
        return response.data

    async def create_skill(self, skill_data: Dict) -> Dict:
        response = self.client.table("skills").insert(skill_data).execute()
        return response.data[0]

    async def find_skill_by_name(self, name: str) -> Optional[Dict]:
        response = self.client.table("skills").select("*").ilike("name", name).execute()
        return response.data[0] if response.data else None


# Singleton instance
supabase_service = SupabaseService()


def get_supabase_client():
    """Get a Supabase client instance for health checks."""
    return supabase_service.client
