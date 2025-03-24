# app/routers/auth.py
from fastapi import APIRouter, Request, Form, Cookie, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from pydantic import BaseModel

# Use absolute imports instead of relative imports
from app.auth import register_user, authenticate_user, JWTBearer

# Initialize router
router = APIRouter(tags=["authentication"])

# Set up templates
templates = Jinja2Templates(directory="templates")

# Pydantic models for request validation
class UserRegistration(BaseModel):
    username: str
    password: str
    id_number: str
    first_name: str
    last_name: str
    birth_date: str
    phone_number: str

class UserLogin(BaseModel):
    username: str
    password: str

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """
    Render the signup page
    """
    return templates.TemplateResponse(
        "signup.html", 
        {"request": request, "title": "ثبت نام"}
    )

@router.post("/signup")
async def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    id_number: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    birth_date: str = Form(...),
    phone_number: str = Form(...)
):
    """
    Handle user registration
    """
    try:
        user_data = register_user(
            username=username,
            password=password,
            id_number=id_number,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            phone_number=phone_number
        )
        
        # Redirect to login page after successful registration
        response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
        # Set JWT token as a cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user_data['access_token']}",
            httponly=True,
            max_age=3600,  # 1 hour
            expires=3600,  # 1 hour
        )
        
        return response
        
    except HTTPException as e:
        # If there's a validation error, show the signup page with error message
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "title": "ثبت نام",
                "error": e.detail,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "id_number": id_number,
                "birth_date": birth_date,
                "phone_number": phone_number
            }
        )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Render the login page
    """
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "title": "ورود به سیستم"}
    )

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Handle user login
    """
    try:
        user_data = authenticate_user(username=username, password=password)
        
        # Redirect to exam page after successful login
        response = RedirectResponse(url="/exam", status_code=status.HTTP_303_SEE_OTHER)
        
        # Set JWT token as a cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user_data['access_token']}",
            httponly=True,
            max_age=3600,  # 1 hour
            expires=3600,  # 1 hour
        )
        
        return response
        
    except HTTPException as e:
        # If authentication fails, show the login page with error message
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "title": "ورود به سیستم",
                "error": e.detail,
                "username": username
            }
        )

@router.get("/logout")
async def logout():
    """
    Handle user logout
    """
    response = RedirectResponse(url="/home")
    response.delete_cookie(key="access_token")
    return response

async def get_current_user(request: Request):
    """
    Get the current user from the token cookie
    """
    token_cookie = request.cookies.get("access_token")
    if not token_cookie or not token_cookie.startswith("Bearer "):
        return None
    
    token = token_cookie.replace("Bearer ", "")
    token_handler = JWTBearer()
    
    try:
        payload = token_handler.verify_jwt_token(token)
        return payload
    except:
        return None