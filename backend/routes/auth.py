import asyncio
import hashlib
import json
import logging
import os
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Depends, status, Response, Request, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from backend.database import get_collection
from backend.models import UserCreate, UserLogin, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from backend.auth import hash_password, verify_password, create_access_token, create_refresh_token, create_reset_token, decode_token, get_current_user, validate_user_token
from backend.config import settings
from backend.email_delivery import deliver_reset_email, delivery_available
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("uvicorn.error")


def is_development() -> bool:
    environment = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", getattr(settings, "APP_ENV", "production")))
    return environment.strip().lower() in {"development", "dev", "local", "test", "testing"}


def cookie_secure() -> bool:
    if not is_development():
        return True
    return os.getenv("COOKIE_SECURE", "false").strip().lower() not in {"false", "0", "no"}


def set_refresh_cookie(response: Response, token: str) -> None:
    lifetime = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        key="refresh_token", value=token, httponly=True,
        max_age=lifetime, expires=lifetime, samesite="lax", secure=cookie_secure(), path="/",
    )


def user_token_data(user: dict) -> dict:
    return {"sub": user["email"], "uid": str(user["_id"]), "ver": user.get("auth_version", 0)}


def reset_base_url():
    base_url = os.getenv("RESET_PASSWORD_BASE_URL", getattr(settings, "RESET_PASSWORD_BASE_URL", ""))
    if not base_url:
        base_url = getattr(settings, "APP_URL", "")
    base_url = base_url.rstrip("/")
    if not base_url and is_development():
        base_url = "http://localhost:8000"
    try:
        parsed = urlsplit(base_url)
        parsed.port
    except ValueError:
        return None
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.scheme not in {"http", "https"}
            or (parsed.scheme != "https" and not is_development())):
        return None
    return base_url

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate):
    users_coll = get_collection("users")
    
    # Check if user already exists
    existing_user = await users_coll.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Create user document
    user_doc = {
        "name": user_in.name,
        "email": user_in.email,
        "password_hash": await run_in_threadpool(hash_password, user_in.password),
        "created_at": datetime.now(timezone.utc),
        "profile": {
            "experience_level": user_in.experience_level,
            "interests": user_in.interests
        }
    }
    
    result = await users_coll.insert_one(user_doc)
    user_doc["id"] = str(result.inserted_id)
    return user_doc

@router.post("/login")
async def login(credentials: UserLogin, response: Response):
    users_coll = get_collection("users")
    
    user = await users_coll.find_one({"email": credentials.email})
    if not user or not await run_in_threadpool(verify_password, credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    access_token = create_access_token(data=user_token_data(user))
    refresh_token = create_refresh_token(data=user_token_data(user))
    
    # Store refresh token in HttpOnly cookie
    set_refresh_cookie(response, refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,  # Also return it in JSON for standard JS environments if needed
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "profile": user["profile"]
        }
    }

@router.post("/refresh")
async def refresh_token_route(request: Request, response: Response):
    # Try getting refresh token from cookie first, then fall back to request body
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        async def read_body():
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 16384:
                    raise HTTPException(status_code=413, detail="Refresh request too large")
            return body

        try:
            body = json.loads(await asyncio.wait_for(read_body(), timeout=5))
        except (ValueError, asyncio.TimeoutError):
            raise HTTPException(status_code=401, detail="Invalid refresh request")
        if not isinstance(body, dict):
            raise HTTPException(status_code=401, detail="Invalid refresh request")
        refresh_token = body.get("refresh_token")
            
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
        
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, refresh token required"
        )
        
    email = payload.get("sub")
    
    users_coll = get_collection("users")
    user = await users_coll.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    validate_user_token(payload, user)
    # Generate new access token
    new_access_token = create_access_token(data=user_token_data(user))
    new_refresh_token = create_refresh_token(data=user_token_data(user))
    
    # Update cookie
    set_refresh_cookie(response, new_refresh_token)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(response: Response):
    response.headers["Cache-Control"] = "no-store"
    response.delete_cookie("refresh_token", path="/", secure=cookie_secure(), httponly=True, samesite="lax")
    return {"message": "Logged out successfully"}

async def send_reset_email(to_email: str, reset_link: str):
    return await deliver_reset_email(to_email, reset_link)

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, response: Response, background_tasks: BackgroundTasks):
    response.headers["Cache-Control"] = "no-store"
    response_data = {"message": "If the email exists in our system, a reset link has been sent."}
    base_url = reset_base_url()
    if not delivery_available() or not base_url:
        logger.warning("Password reset delivery unavailable: configure email delivery and a trusted reset base URL")
        return response_data
    users_coll = get_collection("users")
    user = await users_coll.find_one({"email": req.email})
    if user:
        token = create_reset_token(req.email)
        await users_coll.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "password_reset_token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
                "password_reset_expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
            }},
        )
        background_tasks.add_task(send_reset_email, req.email, f"{base_url}/reset-password?token={token}")
    return response_data

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        payload = decode_token(req.token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or expired reset token: {e.detail}"
        )
        
    if payload.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type"
        )
        
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token subject"
        )
        
    users_coll = get_collection("users")
    user = await users_coll.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
        
    # Update user's password
    digest = hashlib.sha256(req.token.encode("utf-8")).hexdigest()
    if user.get("password_reset_token_hash") != digest:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    new_hash = await run_in_threadpool(hash_password, req.password)
    result = await users_coll.update_one(
        {"_id": user["_id"], "password_reset_token_hash": digest,
         "password_reset_expires_at": {"$gt": datetime.now(timezone.utc)}},
        {"$set": {"password_hash": new_hash}, "$inc": {"auth_version": 1},
         "$unset": {"password_reset_token_hash": "", "password_reset_expires_at": ""}},
    )
    if result.modified_count != 1:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    response.delete_cookie("refresh_token", path="/", secure=cookie_secure(), httponly=True, samesite="lax")
    
    return {"message": "Password has been reset successfully."}

