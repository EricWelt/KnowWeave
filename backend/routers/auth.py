"""认证路由：/auth/register /auth/login /auth/me"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..database import get_session
from ..models import User
from ..schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> dict:
    # 用户名唯一性检查
    existing = await session.scalar(
        select(User).where(User.username == request.username)
    )
    if existing:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
    )
    session.add(user)
    await session.commit()
    return {"message": "注册成功"}


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    user = await session.scalar(
        select(User).where(User.username == request.username)
    )
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return TokenResponse(
        token=create_access_token(user.id),
        user_id=user.id,
        username=user.username,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )
