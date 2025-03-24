# app/auth.py
import re
import bcrypt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import jwt
from typing import Optional, Dict, Any

from .database import get_user_by_username, create_user

# Configuration
SECRET_KEY = "your_secret_key"  # In production, use a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def validate_username(username: str) -> bool:
    """Validate username according to requirements"""
    # Must be 3-10 characters
    if not 3 <= len(username) <= 10:
        return False
    
    # Can only contain letters, numbers, and underscore
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False
    
    # Cannot be only numbers
    if username.isdigit():
        return False
    
    return True


def validate_password(password: str) -> bool:
    """Validate password according to requirements"""
    # Must be 5-30 characters
    if not 5 <= len(password) <= 30:
        return False
    
    # Must contain at least one letter, one number, and one special character
    if not re.search(r'[a-zA-Z]', password):  # At least one letter
        return False
    if not re.search(r'\d', password):  # At least one digit
        return False
    if not re.search(r'[^a-zA-Z0-9]', password):  # At least one special character
        return False
    
    return True


def validate_id_number(id_number: str) -> bool:
    """Validate Iranian national ID number (کد ملی)"""
    # Basic validation for Iranian national ID
    if not re.match(r'^\d{10}$', id_number):
        return False
    
    # Advanced validation could be added here
    return True


def validate_phone_number(phone_number: str) -> bool:
    """Validate Iranian phone number"""
    # Must be exactly 11 digits and start with '09'
    if not re.match(r'^09\d{9}$', phone_number):
        return False
    
    return True


def hash_password(password: str) -> str:
    """Hash a password for storage"""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication"""
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Dict[str, Any]:
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Invalid authentication scheme."
                )
            
            payload = self.verify_jwt_token(credentials.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Invalid token or expired token."
                )
            
            return payload
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Invalid authorization code."
            )

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload if valid"""
        try:
            payload = decode_token(token)
            return payload
        except:
            return None


def register_user(username: str, password: str, id_number: str, 
                 first_name: str, last_name: str, birth_date: str, 
                 phone_number: str) -> Dict[str, Any]:
    """Register a new user with validation"""
    # Validate user inputs
    if not validate_username(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="نام کاربری نامعتبر است. باید بین 3 تا 10 کاراکتر باشد و فقط شامل حروف، اعداد و _ باشد."
        )
    
    if not validate_password(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رمز عبور نامعتبر است. باید بین 5 تا 30 کاراکتر باشد و شامل حروف، اعداد و کاراکترهای خاص باشد."
        )
    
    if not validate_id_number(id_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="کد ملی نامعتبر است. باید دقیقاً 10 رقم باشد."
        )
    
    if not validate_phone_number(phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="شماره تلفن نامعتبر است. باید با 09 شروع شود و دقیقاً 11 رقم باشد."
        )
    
    # Check if username already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="این نام کاربری قبلاً استفاده شده است."
        )
    
    # Hash the password
    hashed_password = hash_password(password)
    
    # Create the user
    user_id = create_user(
        username=username,
        password=hashed_password,
        id_number=id_number,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        phone_number=phone_number
    )
    
    # Generate token for user
    access_token = create_access_token(
        data={"sub": username, "id": user_id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": username
    }


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """Authenticate a user by username and password"""
    user = get_user_by_username(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token for user
    access_token = create_access_token(
        data={"sub": username, "id": user["id"]}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["id"],
        "username": username
    }