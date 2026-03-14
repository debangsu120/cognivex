from fastapi import APIRouter, Depends, HTTPException
from supabase import AsyncClient
from typing import List
from app.deps import get_supabase, get_current_user
from app.models.user import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models.response import APIResponse, PaginatedResponse

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=APIResponse[CompanyResponse])
async def create_company(
    company_data: CompanyCreate,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Create a new company."""
    try:
        company = company_data.model_dump()
        company["owner_id"] = current_user.id

        response = await supabase.table("companies").insert(company).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create company")

        return APIResponse(data=response.data[0], message="Company created successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse[List[CompanyResponse]])
async def list_companies(
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """List all companies for the current user."""
    try:
        response = await supabase.table("companies").select("*").eq("owner_id", current_user.id).execute()

        return APIResponse(data=response.data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}", response_model=APIResponse[CompanyResponse])
async def get_company(
    company_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get a company by ID."""
    try:
        response = await supabase.table("companies").select("*").eq("id", company_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Company not found")

        return APIResponse(data=response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{company_id}", response_model=APIResponse[CompanyResponse])
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Update a company."""
    try:
        # Check ownership
        company = await supabase.table("companies").select("owner_id").eq("id", company_id).execute()
        if not company.data:
            raise HTTPException(status_code=404, detail="Company not found")
        if company.data[0]["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this company")

        # Filter out None values
        update_data = {k: v for k, v in company_data.model_dump().items() if v is not None}

        response = await supabase.table("companies").update(update_data).eq("id", company_id).execute()

        return APIResponse(data=response.data[0], message="Company updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Delete a company."""
    try:
        # Check ownership
        company = await supabase.table("companies").select("owner_id").eq("id", company_id).execute()
        if not company.data:
            raise HTTPException(status_code=404, detail="Company not found")
        if company.data[0]["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this company")

        await supabase.table("companies").delete().eq("id", company_id).execute()

        return {"message": "Company deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
