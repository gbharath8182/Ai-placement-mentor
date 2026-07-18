from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from backend.database import get_collection
from backend.models import UserCreate, UserLogin, UserResponse, TokenResponse, UserProfile, ForgotPasswordRequest, ResetPasswordRequest
from backend.auth import hash_password, verify_password, create_access_token, create_refresh_token, create_reset_token, decode_token, get_current_user
from backend.config import settings
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])

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
        "password_hash": hash_password(user_in.password),
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
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    access_token = create_access_token(data={"sub": user["email"], "uid": str(user["_id"])})
    refresh_token = create_refresh_token(data={"sub": user["email"], "uid": str(user["_id"])})
    
    # Store refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        expires=7 * 24 * 60 * 60,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    
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
    # Try getting refresh token from cookie first, then fall back to Authorization header or request body
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        # Try getting from JSON body
        try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
        except Exception:
            pass
            
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
    uid = payload.get("uid")
    
    users_coll = get_collection("users")
    user = await users_coll.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    # Generate new access token
    new_access_token = create_access_token(data={"sub": email, "uid": uid})
    new_refresh_token = create_refresh_token(data={"sub": email, "uid": uid})
    
    # Update cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        expires=7 * 24 * 60 * 60,
        samesite="lax",
        secure=False
    )
    
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
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

import smtplib
from email.mime.text import MIMEText

import logging
logger = logging.getLogger("uvicorn.error")

def send_reset_email(to_email: str, reset_link: str):
    # Log to uvicorn console so it's guaranteed to show up in terminal logs
    logger.warning("\n" + "="*80)
    logger.warning(f" PASSWORD RESET REQUESTED FOR: {to_email}")
    logger.warning(f" RESET LINK: {reset_link}")
    logger.warning("="*80 + "\n")
    
    if not settings.SMTP_HOST:
        return
        
    try:
        msg = MIMEText(f"Hello,\n\nPlease click the following link to reset your password:\n{reset_link}\n\nThis link is valid for 15 minutes.\n")
        msg['Subject'] = "Password Reset Request"
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = to_email
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}")

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, request: Request):
    users_coll = get_collection("users")
    user = await users_coll.find_one({"email": req.email})
    
    token = create_reset_token(req.email)
    
    # Generate the base URL dynamically based on the request host
    base_url = str(request.base_url).rstrip('/')
    reset_link = f"{base_url}/reset-password?token={token}"
    
    if user:
        send_reset_email(req.email, reset_link)
        
    # Return success message; in dev mode (no SMTP host), also return the reset link in the response
    response_data = {"message": "If the email exists in our system, a reset link has been sent."}
    if not settings.SMTP_HOST and user:
        response_data["reset_link"] = reset_link
        
    return response_data

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
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
    new_hash = hash_password(req.password)
    await users_coll.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": new_hash}}
    )
    
    return {"message": "Password has been reset successfully."}

