from __future__ import annotations

import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

# Simple IP-based rate limiting for login (5 attempts per minute per IP)
_loginAttempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_CLEANUP_INTERVAL = 300  # clean up stale entries every 5 minutes
_last_cleanup_at: float = 0.0


def _check_rate_limit(ip: str, max_attempts: int = 5, window: int = 60) -> None:
    global _last_cleanup_at
    now = time.time()

    # Periodically purge stale IPs to prevent unbounded memory growth
    if now - _last_cleanup_at > _LOGIN_CLEANUP_INTERVAL:
        _last_cleanup_at = now
        stale_ips = [k for k, v in list(_loginAttempts.items()) if not any(now - t < window for t in v)]
        for ip_key in stale_ips:
            _loginAttempts.pop(ip_key, None)

    # Clean old entries for this IP
    _loginAttempts[ip] = [t for t in _loginAttempts[ip] if now - t < window]
    if len(_loginAttempts[ip]) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    _loginAttempts[ip].append(now)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterResponse(BaseModel):
    id: str
    email: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: RegisterResponse


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    existing = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return RegisterResponse(id=str(user.id), email=user.email)


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"sub": str(user.id)})
    return LoginResponse(
        access_token=token,
        user=RegisterResponse(id=str(user.id), email=user.email),
    )
