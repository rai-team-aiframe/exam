# app/superuser_auth.py
from fastapi import HTTPException, Request, status
from datetime import datetime, timedelta
import jwt
from typing import Dict, Any, Optional

from app.superuser_db import get_superuser_by_username

# Configuration
SECRET_KEY = "superuser_secret_key"  # In production, use a secure separate secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours for superuser tokens

def create_superuser_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token for superuser"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_superuser(username: str, password: str) -> Dict[str, Any]:
    """Authenticate a superuser by username and password"""
    superuser = get_superuser_by_username(username)
    
    if not superuser:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_superuser_password(password, superuser["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token for superuser
    access_token = create_superuser_access_token(
        data={"sub": username, "id": superuser["id"], "role": "superuser"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "superuser_id": superuser["id"],
        "username": username
    }

def decode_superuser_token(token: str) -> Dict[str, Any]:
    """Decode and verify superuser JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate superuser credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_superuser(request: Request) -> Optional[Dict[str, Any]]:
    """Get the current superuser from the token cookie"""
    token_cookie = request.cookies.get("superuser_token")
    if not token_cookie or not token_cookie.startswith("Bearer "):
        return None
    
    token = token_cookie.replace("Bearer ", "")
    
    try:
        payload = decode_superuser_token(token)
        if payload.get("role") != "superuser":
            return None
        return payload
    except:
        return None

def verify_superuser_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a superuser password against its hash"""
    import bcrypt
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))