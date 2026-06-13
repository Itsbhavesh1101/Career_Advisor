from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from typing import Literal

from app.api.deps import get_current_user, get_user_role
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


StudentType = Literal["twelfth_student", "college_student"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    student_type: StudentType = "college_student"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str = "Login successful"


class MeResponse(BaseModel):
    email: EmailStr
    role: str
    student_type: StudentType


def _clear_auth_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        domain=settings.auth_cookie_domain,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().auth_rate_limit)
def register(request: Request, payload: RegisterRequest) -> dict:
    del request, payload
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Backend password signup is disabled. Use Supabase Auth.",
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(get_settings().auth_rate_limit)
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
) -> LoginResponse:
    del request, response, payload
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Backend password login is disabled. Use Supabase Auth.",
    )


@router.post("/logout", response_model=LoginResponse)
@limiter.limit(get_settings().auth_rate_limit)
def logout(request: Request, response: Response) -> LoginResponse:
    del request
    _clear_auth_cookie(response)
    return LoginResponse(message="Logged out")


@router.get("/me", response_model=MeResponse)
@limiter.limit(get_settings().auth_me_rate_limit)
def me(request: Request, user: User = Depends(get_current_user)) -> MeResponse:
    del request
    role = get_user_role(user)
    student_type: StudentType = "twelfth_student" if user.student_type == "twelfth_student" else "college_student"
    return MeResponse(email=user.email, role=role, student_type=student_type)
