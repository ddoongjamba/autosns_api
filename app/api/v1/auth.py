"""
인증 API: /auth/register, /auth/login, /auth/refresh, /auth/me
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """회원가입 후 JWT 토큰 반환."""
    return await auth_service.register(db, req)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """로그인 후 JWT 토큰 반환."""
    return await auth_service.login(db, req)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh Token으로 새 Access Token 발급."""
    return await auth_service.refresh_tokens(db, req.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회."""
    return current_user
