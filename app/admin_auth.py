# app/admin_auth.py
from fastapi import HTTPException, Request, status
from datetime import datetime, timedelta
import jwt
from typing import Dict, Any, Optional

from app.admin_db import get_admin_by_username, verify_admin_password

# Configuration
SECRET_KEY = "admin_secret_key"  # In production, use a secure separate secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours for admin tokens

def create_admin_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token for admin"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_admin(username: str, password: str) -> Dict[str, Any]:
    """Authenticate an admin by username and password"""
    admin = get_admin_by_username(username)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_admin_password(password, admin["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token for admin
    access_token = create_admin_access_token(
        data={"sub": username, "id": admin["id"], "role": "admin"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin_id": admin["id"],
        "username": username
    }

def decode_admin_token(token: str) -> Dict[str, Any]:
    """Decode and verify admin JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_admin(request: Request) -> Optional[Dict[str, Any]]:
    """Get the current admin from the token cookie"""
    token_cookie = request.cookies.get("admin_token")
    if not token_cookie or not token_cookie.startswith("Bearer "):
        return None
    
    token = token_cookie.replace("Bearer ", "")
    
    try:
        payload = decode_admin_token(token)
        if payload.get("role") != "admin":
            return None
        return payload
    except:
        return None