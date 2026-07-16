from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from backend.database import get_collection
from backend.models import UserCreate, UserLogin, UserResponse, TokenResponse, UserProfile
from backend.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, get_current_user
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
