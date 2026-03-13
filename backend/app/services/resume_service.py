"""Resume Processing Service for extracting and analyzing resume content."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import io
import json

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from supabase import AsyncClient
from app.exceptions import AIException, SupabaseException
from app.services.groq import groq_service


class ResumeProcessingService:
    """Service for processing resumes including PDF extraction and skill analysis."""

    def __init__(self, supabase_client: AsyncClient):
        """Initialize with Supabase client.

        Args:
            supabase_client: Async Supabase client for database/storage operations
        """
        self.supabase = supabase_client

    async def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file content.

        Args:
            file_content: Raw PDF file bytes

        Returns:
            Extracted text from PDF

        Raises:
            ValueError: If no PDF library is available or extraction fails
        """
        if not file_content:
            return ""

        # Try pdfplumber first (better extraction)
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    return text.strip()
            except Exception as e:
                pass  # Fall back to PyPDF2

        # Try PyPDF2 as fallback
        if PYPDF2_AVAILABLE:
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            except Exception as e:
                raise ValueError(f"Failed to extract text from PDF: {str(e)}")

        raise ValueError(
            "No PDF extraction library available. Install PyPDF2 or pdfplumber."
        )

    def extract_text_from_file(
        self, file_content: bytes, file_extension: str
    ) -> str:
        """Extract text from various file formats.

        Args:
            file_content: Raw file bytes
            file_extension: File extension (txt, pdf, doc, docx)

        Returns:
            Extracted text content
        """
        if file_extension.lower() == "txt":
            return file_content.decode("utf-8", errors="ignore")

        elif file_extension.lower() == "pdf":
            return self.extract_text_from_pdf(file_content)

        elif file_extension.lower() in ["doc", "docx"]:
            # Basic DOCX support - in production use python-docx
            # For now, return empty as DOC parsing requires additional libraries
            return ""

        return ""

    async def upload_to_storage(
        self, file_content: bytes, file_path: str, content_type: str
    ) -> Optional[str]:
        """Upload file to Supabase Storage.

        Args:
            file_content: File bytes to upload
            file_path: Path in storage bucket
            content_type: MIME type of file

        Returns:
            Public URL of uploaded file or None if failed
        """
        try:
            response = await self.supabase.storage.from_("resumes").upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type}
            )

            if response.data:
                # Get public URL
                public_url = self.supabase.storage.from_("resumes").get_public_url(
                    file_path
                )
                return public_url

            return None
        except Exception as e:
            # Log error but don't fail the whole process
            return None

    async def analyze_resume_with_ai(
        self, resume_text: str
    ) -> Dict[str, Any]:
        """Analyze resume using AI to extract structured information.

        Args:
            resume_text: Raw resume text content

        Returns:
            Dictionary containing:
                - skills: List of extracted skills
                - years_of_experience: Estimated years of experience
                - education: Education details
                - technologies: List of technologies/tools
        """
        if not resume_text or len(resume_text.strip()) < 50:
            return {
                "skills": [],
                "years_of_experience": 0,
                "education": "",
                "technologies": []
            }

        try:
            # Use enhanced skill extraction from Groq service
            analysis_result = await groq_service.extract_resume_details(resume_text)

            return {
                "skills": analysis_result.get("skills", []),
                "years_of_experience": analysis_result.get("years_of_experience", 0),
                "education": analysis_result.get("education", ""),
                "technologies": analysis_result.get("technologies", [])
            }
        except Exception as e:
            raise AIException(f"Failed to analyze resume with AI: {str(e)}")

    async def process_resume(
        self,
        file_content: bytes,
        file_name: str,
        user_id: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Complete resume processing pipeline.

        Args:
            file_content: Raw file bytes
            file_name: Original file name
            user_id: User ID who owns the resume
            content_type: MIME type of file

        Returns:
            Dictionary with resume data ready for database insertion
        """
        # Determine file extension
        file_extension = file_name.split(".")[-1].lower() if "." in file_name else ""

        if file_extension not in ["txt", "pdf", "doc", "docx"]:
            raise ValueError(f"Unsupported file type: {file_extension}")

        # Extract text from file
        resume_text = self.extract_text_from_file(file_content, file_extension)

        if not resume_text or len(resume_text.strip()) < 50:
            raise ValueError("Could not extract sufficient text from resume")

        # Upload to storage
        storage_path = f"resumes/{user_id}/{datetime.utcnow().timestamp()}_{file_name}"
        file_url = await self.upload_to_storage(file_content, storage_path, content_type)

        # Analyze with AI
        analysis = await self.analyze_resume_with_ai(resume_text)

        # Prepare resume data
        resume_data = {
            "user_id": user_id,
            "file_name": file_name,
            "file_path": storage_path,
            "file_url": file_url,
            "skills": analysis.get("skills", []),
            "experience_years": analysis.get("years_of_experience", 0),
            "education": analysis.get("education", ""),
            "technologies": analysis.get("technologies", []),
            "parsed_data": {
                "text": resume_text[:10000] if len(resume_text) > 10000 else resume_text,
                "extracted_at": datetime.utcnow().isoformat(),
                "content_type": content_type,
                "file_size": len(file_content)
            }
        }

        return resume_data

    async def get_resume_with_analysis(self, resume_id: str) -> Optional[Dict]:
        """Get resume with full analysis results.

        Args:
            resume_id: Resume ID to retrieve

        Returns:
            Resume data with related analysis
        """
        response = await self.supabase.table("resumes").select("*").eq("id", resume_id).execute()
        return response.data[0] if response.data else None

    async def update_resume_skills(self, resume_id: str, skills: List[str]) -> Dict:
        """Update resume skills after manual review.

        Args:
            resume_id: Resume ID to update
            skills: New list of skills

        Returns:
            Updated resume data
        """
        response = await self.supabase.table("resumes").update({
            "skills": skills,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", resume_id).execute()

        if not response.data:
            raise SupabaseException("Failed to update resume skills")

        return response.data[0]


# Factory function to create service instance
def create_resume_service(supabase_client: AsyncClient) -> ResumeProcessingService:
    """Create a ResumeProcessingService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured ResumeProcessingService instance
    """
    return ResumeProcessingService(supabase_client)
