from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import AsyncClient
from typing import List, Optional
from app.deps import get_supabase, get_current_user
from app.models.user import JobCreate, JobUpdate, JobResponse
from app.models.interview import CandidateMatch
from app.models.response import APIResponse, PaginatedResponse
from app.services.matching import matching_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=APIResponse[JobResponse])
async def create_job(
    job_data: JobCreate,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Create a new job posting."""
    try:
        # Verify company exists and user owns it
        company = await supabase.table("companies").select("*").eq("id", job_data.company_id).execute()
        if not company.data:
            raise HTTPException(status_code=404, detail="Company not found")
        if company.data[0]["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to post jobs for this company")

        job = job_data.model_dump()
        job["owner_id"] = current_user.id

        response = await supabase.table("jobs").insert(job).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create job")

        return APIResponse(data=response.data[0], message="Job created successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse[List[JobResponse]])
async def list_jobs(
    company_id: Optional[str] = Query(None),
    is_active: Optional[bool] = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    supabase: AsyncClient = Depends(get_supabase)
):
    """List all jobs, optionally filtered by company."""
    try:
        query = supabase.table("jobs").select("*, companies(*)")
        if company_id:
            query = query.eq("company_id", company_id)
        if is_active is not None:
            query = query.eq("is_active", is_active)

        # Calculate offset
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        response = await query.execute()

        # Get total count
        count_query = supabase.table("jobs").select("*", count="exact")
        if company_id:
            count_query = count_query.eq("company_id", company_id)
        if is_active is not None:
            count_query = count_query.eq("is_active", is_active)
        count_response = await count_query.execute()
        total = count_response.count or 0

        return APIResponse(data=response.data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=APIResponse[JobResponse])
async def get_job(
    job_id: str,
    supabase: AsyncClient = Depends(get_supabase)
):
    """Get a job by ID."""
    try:
        response = await supabase.table("jobs").select("*, companies(*)").eq("id", job_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Job not found")

        return APIResponse(data=response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{job_id}", response_model=APIResponse[JobResponse])
async def update_job(
    job_id: str,
    job_data: JobUpdate,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Update a job posting."""
    try:
        # Check ownership
        job = await supabase.table("jobs").select("owner_id").eq("id", job_id).execute()
        if not job.data:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.data[0]["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this job")

        # Filter out None values
        update_data = {k: v for k, v in job_data.model_dump().items() if v is not None}

        response = await supabase.table("jobs").update(update_data).eq("id", job_id).execute()

        return APIResponse(data=response.data[0], message="Job updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Delete a job posting."""
    try:
        # Check ownership
        job = await supabase.table("jobs").select("owner_id").eq("id", job_id).execute()
        if not job.data:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.data[0]["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this job")

        await supabase.table("jobs").delete().eq("id", job_id).execute()

        return {"message": "Job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/candidates", response_model=APIResponse[List[CandidateMatch]])
async def get_matching_candidates(
    job_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get candidates matching a job."""
    try:
        # Verify job exists and user owns it
        job = await supabase.table("jobs").select("*, companies(*)").eq("id", job_id).execute()
        if not job.data:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.data[0]["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view candidates for this job")

        # Get all resumes
        resumes_response = await supabase.table("resumes").select("*").execute()
        resumes = resumes_response.data

        # Match each candidate to the job
        matches = []
        for resume in resumes:
            try:
                match = await matching_service.match_candidate_to_job(
                    candidate_id=resume["user_id"],
                    job_id=job_id
                )
                matches.append(match.model_dump())
            except Exception:
                continue

        # Sort by overall match score
        matches.sort(key=lambda x: x.get("overall_match_score", 0), reverse=True)

        return APIResponse(data=matches)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
