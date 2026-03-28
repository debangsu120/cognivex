from pydantic import BaseModel
from typing import Optional, Any, List, Generic, TypeVar


T = TypeVar("T")


class APIResponseData(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None


APIResponse = APIResponseData


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None


class MessageResponse(BaseModel):
    success: bool = True
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: Optional[dict] = None


class AuthResponse(BaseModel):
    session: Optional[dict] = None
    user: Optional[dict] = None
