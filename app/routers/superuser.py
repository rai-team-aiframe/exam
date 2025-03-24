# app/routers/superuser.py
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status, Query, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Dict, List, Optional, Any
import json

from app.superuser_auth import authenticate_superuser, get_current_superuser, verify_superuser_password
from app.superuser_db import (
    get_all_admins_with_profiles, 
    get_admin_with_profile,
    create_admin, 
    update_admin, 
    delete_admin,
    get_superuser_by_id,
    update_superuser_credentials
)
from app.date_utils import format_date_shamsi

# Initialize router
router = APIRouter(tags=["superuser"])

# Set up templates
templates = Jinja2Templates(directory="templates")

# Add date formatting function to Jinja environment
templates.env.globals["format_date_shamsi"] = format_date_shamsi

@router.get("/superuser/login", response_class=HTMLResponse)
async def superuser_login_page(request: Request, current_superuser: Dict = Depends(get_current_superuser)):
    """
    Render the superuser login page or redirect to dashboard if already logged in
    """
    if current_superuser:
        return RedirectResponse(url="/superuser/dashboard")
    
    return templates.TemplateResponse(
        "superuser/login.html", 
        {"request": request, "title": "ورود سوپرادمین"}
    )

@router.post("/superuser/login")
async def superuser_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Handle superuser login
    """
    try:
        superuser_data = authenticate_superuser(username=username, password=password)
        
        # Redirect to superuser dashboard after successful login
        response = RedirectResponse(url="/superuser/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        
        # Set JWT token as a cookie
        response.set_cookie(
            key="superuser_token",
            value=f"Bearer {superuser_data['access_token']}",
            httponly=True,
            max_age=3600 * 12,  # 12 hours
            expires=3600 * 12,
        )
        
        return response
        
    except HTTPException as e:
        # If authentication fails, show the login page with error message
        return templates.TemplateResponse(
            "superuser/login.html",
            {
                "request": request,
                "title": "ورود سوپرادمین",
                "error": e.detail,
                "username": username
            }
        )

@router.get("/superuser/logout")
async def superuser_logout():
    """
    Handle superuser logout
    """
    response = RedirectResponse(url="/superuser/login")
    response.delete_cookie(key="superuser_token")
    return response

@router.get("/superuser/dashboard", response_class=HTMLResponse)
async def superuser_dashboard(
    request: Request, 
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Render the superuser dashboard
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    # Get all admins with their profiles
    admins = get_all_admins_with_profiles()
    
    return templates.TemplateResponse(
        "superuser/dashboard.html", 
        {
            "request": request, 
            "title": "پنل سوپرادمین",
            "superuser": current_superuser,
            "admins": admins
        }
    )

@router.get("/superuser/admin/new", response_class=HTMLResponse)
async def create_admin_form(
    request: Request,
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Show form to create a new admin account
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    return templates.TemplateResponse(
        "superuser/admin_form.html",
        {
            "request": request,
            "title": "ایجاد مدیر جدید",
            "superuser": current_superuser,
            "is_new": True
        }
    )

@router.post("/superuser/admin/new")
async def create_admin_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    job_field: str = Form(""),
    id_number: str = Form(""),
    phone_number: str = Form(""),
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Handle form submission to create a new admin
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    try:
        # Create admin
        admin_id = create_admin(
            username=username,
            password=password,
            full_name=full_name,
            job_field=job_field,
            id_number=id_number,
            phone_number=phone_number
        )
        
        # Redirect to dashboard
        return RedirectResponse(
            url="/superuser/dashboard",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    except ValueError as e:
        # Display form with error
        return templates.TemplateResponse(
            "superuser/admin_form.html",
            {
                "request": request,
                "title": "ایجاد مدیر جدید",
                "superuser": current_superuser,
                "is_new": True,
                "error": str(e),
                "username": username,
                "full_name": full_name,
                "job_field": job_field,
                "id_number": id_number,
                "phone_number": phone_number
            }
        )
    except Exception as e:
        # Display form with error
        return templates.TemplateResponse(
            "superuser/admin_form.html",
            {
                "request": request,
                "title": "ایجاد مدیر جدید",
                "superuser": current_superuser,
                "is_new": True,
                "error": f"خطا در ایجاد مدیر: {str(e)}",
                "username": username,
                "full_name": full_name,
                "job_field": job_field,
                "id_number": id_number,
                "phone_number": phone_number
            }
        )

@router.get("/superuser/admin/{admin_id}", response_class=HTMLResponse)
async def edit_admin_form(
    request: Request,
    admin_id: int = Path(...),
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Show form to edit an admin account
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    # Get admin data
    admin = get_admin_with_profile(admin_id)
    
    if not admin:
        return templates.TemplateResponse(
            "superuser/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "مدیر مورد نظر یافت نشد."
            }
        )
    
    return templates.TemplateResponse(
        "superuser/admin_form.html",
        {
            "request": request,
            "title": f"ویرایش مدیر: {admin['username']}",
            "superuser": current_superuser,
            "is_new": False,
            "admin": admin,
            "admin_id": admin_id
        }
    )

@router.post("/superuser/admin/{admin_id}")
async def edit_admin_submit(
    request: Request,
    admin_id: int = Path(...),
    username: str = Form(...),
    password: str = Form(None),
    full_name: str = Form(""),
    job_field: str = Form(""),
    id_number: str = Form(""),
    phone_number: str = Form(""),
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Handle form submission to edit an admin
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    try:
        # Update admin
        update_admin(
            admin_id=admin_id,
            username=username,
            password=password,
            full_name=full_name,
            job_field=job_field,
            id_number=id_number,
            phone_number=phone_number
        )
        
        # Redirect to dashboard
        return RedirectResponse(
            url="/superuser/dashboard",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    except ValueError as e:
        # Get admin data
        admin = get_admin_with_profile(admin_id)
        
        # Display form with error
        return templates.TemplateResponse(
            "superuser/admin_form.html",
            {
                "request": request,
                "title": f"ویرایش مدیر: {username}",
                "superuser": current_superuser,
                "is_new": False,
                "admin": admin,
                "admin_id": admin_id,
                "error": str(e),
                "username": username,
                "full_name": full_name,
                "job_field": job_field,
                "id_number": id_number,
                "phone_number": phone_number
            }
        )
    except Exception as e:
        # Get admin data
        admin = get_admin_with_profile(admin_id)
        
        # Display form with error
        return templates.TemplateResponse(
            "superuser/admin_form.html",
            {
                "request": request,
                "title": f"ویرایش مدیر: {username}",
                "superuser": current_superuser,
                "is_new": False,
                "admin": admin,
                "admin_id": admin_id,
                "error": f"خطا در ویرایش مدیر: {str(e)}",
                "username": username,
                "full_name": full_name,
                "job_field": job_field,
                "id_number": id_number,
                "phone_number": phone_number
            }
        )

@router.get("/superuser/admin/{admin_id}/delete")
async def delete_admin_confirm(
    request: Request,
    admin_id: int = Path(...),
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Show confirmation page for deleting an admin
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    # Get admin data
    admin = get_admin_with_profile(admin_id)
    
    if not admin:
        return templates.TemplateResponse(
            "superuser/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "مدیر مورد نظر یافت نشد."
            }
        )
    
    return templates.TemplateResponse(
        "superuser/delete_confirm.html",
        {
            "request": request,
            "title": f"حذف مدیر: {admin['username']}",
            "superuser": current_superuser,
            "admin": admin,
            "admin_id": admin_id
        }
    )

@router.post("/superuser/admin/{admin_id}/delete")
async def delete_admin_submit(
    request: Request,
    admin_id: int = Path(...),
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Handle admin deletion
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    try:
        # Delete admin
        delete_admin(admin_id)
        
        # Redirect to dashboard
        return RedirectResponse(
            url="/superuser/dashboard",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    except Exception as e:
        # Display error page
        return templates.TemplateResponse(
            "superuser/error.html",
            {
                "request": request,
                "title": "خطا در حذف مدیر",
                "message": str(e)
            }
        )

@router.get("/superuser/profile", response_class=HTMLResponse)
async def superuser_profile_page(
    request: Request,
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Show superuser profile page
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    # Get superuser data
    superuser_data = get_superuser_by_id(current_superuser["id"])
    
    if not superuser_data:
        return templates.TemplateResponse(
            "superuser/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "اطلاعات سوپرادمین یافت نشد."
            }
        )
    
    return templates.TemplateResponse(
        "superuser/profile.html",
        {
            "request": request,
            "title": "پروفایل سوپرادمین",
            "superuser": current_superuser,
            "superuser_data": superuser_data
        }
    )

@router.post("/superuser/profile", response_class=HTMLResponse)
async def superuser_profile_update(
    request: Request,
    username: str = Form(...),
    current_password: str = Form(...),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
    current_superuser: Dict = Depends(get_current_superuser)
):
    """
    Handle superuser profile update
    """
    if not current_superuser:
        return RedirectResponse(url="/superuser/login")
    
    # Get superuser data
    superuser_data = get_superuser_by_id(current_superuser["id"])
    
    if not superuser_data:
        return templates.TemplateResponse(
            "superuser/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "اطلاعات سوپرادمین یافت نشد."
            }
        )
    
    # Verify current password
    if not verify_superuser_password(current_password, superuser_data["password"]):
        return templates.TemplateResponse(
            "superuser/profile.html",
            {
                "request": request,
                "title": "پروفایل سوپرادمین",
                "superuser": current_superuser,
                "superuser_data": superuser_data,
                "error": "رمز عبور فعلی اشتباه است."
            }
        )
    
    # Check if passwords match if changing password
    if new_password and new_password != confirm_password:
        return templates.TemplateResponse(
            "superuser/profile.html",
            {
                "request": request,
                "title": "پروفایل سوپرادمین",
                "superuser": current_superuser,
                "superuser_data": superuser_data,
                "error": "رمز عبور جدید با تکرار آن مطابقت ندارد."
            }
        )
    
    try:
        # Update superuser
        updated_password = new_password if new_password else None
        update_superuser_credentials(
            superuser_id=current_superuser["id"],
            username=username,
            password=updated_password
        )
        
        # Get updated data
        updated_superuser_data = get_superuser_by_id(current_superuser["id"])
        
        # Show success message
        return templates.TemplateResponse(
            "superuser/profile.html",
            {
                "request": request,
                "title": "پروفایل سوپرادمین",
                "superuser": current_superuser,
                "superuser_data": updated_superuser_data,
                "success": "اطلاعات کاربری با موفقیت بروزرسانی شد."
            }
        )
    
    except ValueError as e:
        return templates.TemplateResponse(
            "superuser/profile.html",
            {
                "request": request,
                "title": "پروفایل سوپرادمین",
                "superuser": current_superuser,
                "superuser_data": superuser_data,
                "error": str(e)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "superuser/profile.html",
            {
                "request": request,
                "title": "پروفایل سوپرادمین",
                "superuser": current_superuser,
                "superuser_data": superuser_data,
                "error": f"خطا در بروزرسانی اطلاعات: {str(e)}"
            }
        )