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
from app.services.resume_service import create_resume_service, ResumeProcessingService

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=APIResponse[ResumeResponse])
async def upload_resume(
    file: UploadFile = File(...),
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Upload and parse a resume.

    Supports PDF, TXT, DOC, and DOCX files.
    Extracts text and uses AI to analyze skills, experience, and education.
    """
    try:
        # Read file content
        content = await file.read()

        # Determine file extension
        file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""

        if file_extension not in ["txt", "pdf", "doc", "docx"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Use the resume processing service
        service: ResumeProcessingService = create_resume_service(supabase)

        try:
            # Process the resume (extract text, analyze with AI, upload to storage)
            resume_data = await service.process_resume(
                file_content=content,
                file_name=file.filename,
                user_id=current_user.id,
                content_type=file.content_type or "application/octet-stream"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Insert into database
        response = await supabase.table("resumes").insert(resume_data).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create resume")

        return APIResponse(data=response.data[0], message="Resume uploaded and analyzed successfully")
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
