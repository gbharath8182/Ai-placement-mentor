import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config import settings
from backend.database import get_collection

security = HTTPBearer(auto_error=False)

MAX_TOKEN_LENGTH = 8192


def _password_bytes(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if not 1 <= len(encoded) <= 72:
        raise ValueError("Password must be between 1 and 72 UTF-8 bytes")
    return encoded

def hash_password(password: str) -> str:
    pwd_bytes = _password_bytes(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(plain_password), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access", "iat": datetime.now(timezone.utc), "jti": secrets.token_hex(16)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "iat": datetime.now(timezone.utc), "jti": secrets.token_hex(16)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_reset_token(email: str) -> str:
    to_encode = {"sub": email}
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "reset", "jti": secrets.token_hex(16)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        if not isinstance(token, str) or not 1 <= len(token) <= MAX_TOKEN_LENGTH:
            raise jwt.InvalidTokenError()
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
        if not isinstance(payload["sub"], str) or not 1 <= len(payload["sub"]) <= 254:
            raise jwt.InvalidTokenError()
        if payload["type"] not in ("access", "refresh", "reset"):
            raise jwt.InvalidTokenError()
        if type(payload["exp"]) not in (int, float):
            raise jwt.InvalidTokenError()
        if "uid" in payload and (not isinstance(payload["uid"], str) or not payload["uid"]):
            raise jwt.InvalidTokenError()
        if type(payload.get("ver", 0)) is not int or payload.get("ver", 0) < 0:
            raise jwt.InvalidTokenError()
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def validate_user_token(payload: dict, user: dict) -> None:
    if (payload.get("uid", str(user["_id"])) != str(user["_id"])
            or payload.get("ver", 0) != user.get("auth_version", 0)):
        raise HTTPException(status_code=401, detail="Invalid token credentials", headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, access token required",
        )
        
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identity",
        )
        
    users_coll = get_collection("users")
    user = await users_coll.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    validate_user_token(payload, user)
    # Return user with id string representation
    user["id"] = str(user["_id"])
    return user
