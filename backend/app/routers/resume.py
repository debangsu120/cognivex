from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from supabase import AsyncClient
from typing import List
import io
import base64
from app.deps import get_supabase, get_current_user
from app.models.user import ResumeResponse
from app.models.response import APIResponse
from app.services.groq import groq_service
from app.services.supabase import supabase_service

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=APIResponse[ResumeResponse])
async def upload_resume(
    file: UploadFile = File(...),
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Upload and parse a resume."""
    try:
        # Read file content
        content = await file.read()

        # For PDF files, we'd need to extract text first
        # For now, we'll handle text-based files
        file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""

        if file_extension not in ["txt", "pdf", "doc", "docx"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Upload file to Supabase Storage
        file_path = f"resumes/{current_user.id}/{file.filename}"

        try:
            storage_response = await supabase.storage.from_("resumes").upload(
                path=file_path,
                file=content,
                file_options={"content_type": file.content_type}
            )
        except Exception as storage_error:
            # If storage upload fails, continue without storing file
            file_path = ""

        # Extract text from resume
        # For now, we'll assume it's a text file or extract text from PDF
        resume_text = ""

        if file_extension == "txt":
            resume_text = content.decode("utf-8", errors="ignore")
        elif file_extension == "pdf":
            # In production, use a PDF parser like PyPDF2 or pdfplumber
            # For now, we'll skip PDF text extraction
            resume_text = ""  # Would need PDF parsing library

        # Extract skills using AI
        skills = []
        if resume_text:
            try:
                skills = await groq_service.extract_skills_from_resume(resume_text)
            except Exception:
                skills = []

        # Create resume record
        resume_data = {
            "user_id": current_user.id,
            "file_name": file.filename,
            "file_path": file_path,
            "skills": skills,
            "parsed_data": {
                "text": resume_text[:5000] if len(resume_text) > 5000 else resume_text  # Limit text stored
            }
        }

        response = await supabase.table("resumes").insert(resume_data).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create resume")

        return APIResponse(data=response.data[0], message="Resume uploaded successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse[List[ResumeResponse]])
async def list_resumes(
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """List all resumes for the current user."""
    try:
        response = await supabase.table("resumes").select("*").eq("user_id", current_user.id).execute()

        return APIResponse(data=response.data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{resume_id}", response_model=APIResponse[ResumeResponse])
async def get_resume(
    resume_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get a resume by ID."""
    try:
        response = await supabase.table("resumes").select("*").eq("id", resume_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Check ownership
        if response.data[0]["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this resume")

        return APIResponse(data=response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Delete a resume."""
    try:
        # Check ownership
        resume = await supabase.table("resumes").select("user_id, file_path").eq("id", resume_id).execute()
        if not resume.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        if resume.data[0]["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this resume")

        # Delete from storage
        file_path = resume.data[0].get("file_path")
        if file_path:
            try:
                await supabase.storage.from_("resumes").remove([file_path])
            except Exception:
                pass  # Continue even if storage deletion fails

        # Delete from database
        await supabase.table("resumes").delete().eq("id", resume_id).execute()

        return {"message": "Resume deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{resume_id}/skills", response_model=APIResponse[ResumeResponse])
async def update_resume_skills(
    resume_id: str,
    skills: List[str],
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Update skills for a resume."""
    try:
        # Check ownership
        resume = await supabase.table("resumes").select("user_id").eq("id", resume_id).execute()
        if not resume.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        if resume.data[0]["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this resume")

        response = await supabase.table("resumes").update({"skills": skills}).eq("id", resume_id).execute()

        return APIResponse(data=response.data[0], message="Skills updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
