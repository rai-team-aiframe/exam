# app/routers/admin.py
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status, Query, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse
from typing import Dict, List, Optional, Any
import json
from io import BytesIO
from datetime import datetime
import os

from app.admin_auth import authenticate_admin, get_current_admin
from app.database import get_user_by_username, get_user_by_id_number, has_completed_exam, get_exam_review, mark_exam_reviewed, reset_user_exam
from app.pdf_generator import generate_user_report_pdf
from app.admin_db import init_admin_db
from app.date_utils import format_date_shamsi

# Initialize router
router = APIRouter(tags=["admin"])

# Set up templates
templates = Jinja2Templates(directory="templates")

# Add date formatting function to Jinja environment
templates.env.globals["format_date_shamsi"] = format_date_shamsi

# Initialize admin database on startup
init_admin_db()

@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, current_admin: Dict = Depends(get_current_admin)):
    """
    Render the admin login page or redirect to dashboard if already logged in
    """
    if current_admin:
        return RedirectResponse(url="/admin/dashboard")
    
    return templates.TemplateResponse(
        "admin/login.html", 
        {"request": request, "title": "ورود مدیر"}
    )

@router.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Handle admin login
    """
    try:
        admin_data = authenticate_admin(username=username, password=password)
        
        # Redirect to admin dashboard after successful login
        response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        
        # Set JWT token as a cookie
        response.set_cookie(
            key="admin_token",
            value=f"Bearer {admin_data['access_token']}",
            httponly=True,
            max_age=3600 * 24,  # 24 hours
            expires=3600 * 24,
        )
        
        return response
        
    except HTTPException as e:
        # If authentication fails, show the login page with error message
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "title": "ورود مدیر",
                "error": e.detail,
                "username": username
            }
        )

@router.get("/admin/logout")
async def admin_logout():
    """
    Handle admin logout
    """
    response = RedirectResponse(url="/admin/login")
    response.delete_cookie(key="admin_token")
    return response

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, 
    current_admin: Dict = Depends(get_current_admin),
    search: Optional[str] = Query(None)
):
    """
    Render the admin dashboard with search functionality
    """
    if not current_admin:
        return RedirectResponse(url="/admin/login")
    
    search_results = []
    search_performed = search is not None
    
    if search_performed and search:
        # Check if search term is an ID number (all digits)
        if search.isdigit():
            user = get_user_by_id_number(search)
            if user:
                # Add flag to show if user has completed the exam
                user["has_completed_exam"] = has_completed_exam(user["id"])
                search_results.append(user)
        else:
            # Search by username
            user = get_user_by_username(search)
            if user:
                # Add flag to show if user has completed the exam
                user["has_completed_exam"] = has_completed_exam(user["id"])
                search_results.append(user)
    
    return templates.TemplateResponse(
        "admin/dashboard.html", 
        {
            "request": request, 
            "title": "پنل مدیریت",
            "admin": current_admin,
            "search": search,
            "search_performed": search_performed,
            "search_results": search_results
        }
    )

@router.get("/admin/user/{user_id}", response_class=HTMLResponse)
async def view_user_details(
    request: Request,
    user_id: int,
    current_admin: Dict = Depends(get_current_admin)
):
    """
    View detailed information about a user and their exam answers
    """
    if not current_admin:
        return RedirectResponse(url="/admin/login")
    
    # Get user details and exam responses
    user_details, exam_responses = get_user_report_data(user_id)
    
    if not user_details:
        return templates.TemplateResponse(
            "admin/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "کاربر مورد نظر یافت نشد."
            }
        )
    
    return templates.TemplateResponse(
        "admin/user_details.html",
        {
            "request": request,
            "title": f"اطلاعات کاربر: {user_details['username']}",
            "admin": current_admin,
            "user": user_details,
            "exam_responses": exam_responses
        }
    )

@router.get("/admin/user/{user_id}/review", response_class=HTMLResponse)
async def admin_review_form(
    request: Request,
    user_id: int,
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Show the review form for an exam
    """
    if not current_admin:
        return RedirectResponse(url="/admin/login")
    
    # Get user details
    user_details, _ = get_user_report_data(user_id)
    
    if not user_details:
        return templates.TemplateResponse(
            "admin/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "کاربر مورد نظر یافت نشد."
            }
        )
    
    # Check if user has completed the exam
    if not has_completed_exam(user_id):
        return templates.TemplateResponse(
            "admin/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "این کاربر هنوز آزمون را تکمیل نکرده است."
            }
        )
    
    # Get existing review if any
    existing_review = get_exam_review(user_id)
    review_text = existing_review['review_text'] if existing_review else ""
    
    return templates.TemplateResponse(
        "admin/review_form.html",
        {
            "request": request,
            "title": f"بررسی آزمون کاربر: {user_details['username']}",
            "admin": current_admin,
            "user": user_details,
            "review_text": review_text
        }
    )

@router.post("/admin/user/{user_id}/review")
async def submit_exam_review(
    request: Request,
    user_id: int,
    review_text: str = Form(...),
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Submit a review for a user's exam
    """
    if not current_admin:
        return RedirectResponse(url="/admin/login")
    
    try:
        # Save the review
        mark_exam_reviewed(
            user_id=user_id,
            admin_id=current_admin["id"],
            review_text=review_text
        )
        
        # Redirect back to user details page
        return RedirectResponse(
            url=f"/admin/user/{user_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        print(f"Error saving review: {e}")
        return templates.TemplateResponse(
            "admin/error.html",
            {
                "request": request,
                "title": "خطا در ثبت بررسی",
                "message": f"متأسفانه در ثبت بررسی آزمون خطایی رخ داده است: {str(e)}"
            }
        )

@router.get("/admin/user/{user_id}/reset")
async def confirm_reset_exam(
    request: Request,
    user_id: int,
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Show confirmation page for resetting a user's exam
    """
    if not current_admin:
        return RedirectResponse(url="/admin/login")
    
    # Get user details
    user_details, _ = get_user_report_data(user_id)
    
    if not user_details:
        return templates.TemplateResponse(
            "admin/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "کاربر مورد نظر یافت نشد."
            }
        )
    
    return templates.TemplateResponse(
        "admin/reset_confirm.html",
        {
            "request": request,
            "title": f"تایید بازنشانی آزمون کاربر: {user_details['username']}",
            "admin": current_admin,
            "user": user_details
        }
    )

@router.post("/admin/user/{user_id}/reset")
async def reset_exam(
    request: Request,
    user_id: int,
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Reset a user's exam (delete all responses and allow them to retake)
    """
    if not current_admin:
        return RedirectResponse(url="/admin/login")
    
    try:
        # Reset the exam
        success = reset_user_exam(user_id)
        
        if not success:
            raise Exception("Failed to reset exam")
        
        # Redirect back to user details page
        return RedirectResponse(
            url=f"/admin/user/{user_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        print(f"Error resetting exam: {e}")
        return templates.TemplateResponse(
            "admin/error.html",
            {
                "request": request,
                "title": "خطا در بازنشانی آزمون",
                "message": f"متأسفانه در بازنشانی آزمون خطایی رخ داده است: {str(e)}"
            }
        )

@router.get("/admin/user/{user_id}/pdf")
async def download_user_report_pdf(
    request: Request,
    user_id: int,
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Generate and download an Excel report for a user
    (We keep the route name 'pdf' for backward compatibility)
    """
    if not current_admin:
        return RedirectResponse(url="/admin/login")
    
    # Get user details and exam responses
    user_details, exam_responses = get_user_report_data(user_id)
    
    if not user_details:
        return templates.TemplateResponse(
            "admin/error.html",
            {
                "request": request,
                "title": "خطا",
                "message": "کاربر مورد نظر یافت نشد."
            }
        )
    
    try:
        # Generate Excel file (using the pdf_generator function)
        excel_buffer = generate_user_report_pdf(user_details, exam_responses)
        
        if not excel_buffer:
            raise ValueError("Excel generation failed")
        
        # Return Excel file
        filename = f"user_report_{user_details['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        # Handle any errors in Excel generation
        print(f"Error generating Excel: {e}")
        return templates.TemplateResponse(
            "admin/error.html",
            {
                "request": request,
                "title": "خطا در تولید فایل اکسل",
                "message": f"متأسفانه در تولید فایل اکسل خطایی رخ داده است: {str(e)}"
            }
        )

def get_user_report_data(user_id: int):
    """
    Get user details and exam responses for reporting
    """
    from app.database import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user details
    cursor.execute("""
        SELECT id, username, id_number, first_name, last_name, birth_date, phone_number, created_at
        FROM users
        WHERE id = ?
    """, (user_id,))
    
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return None, None
    
    user_details = dict(user)
    
    # Check if user has a review
    exam_review = get_exam_review(user_id)
    if exam_review:
        user_details['has_review'] = True
        user_details['review_text'] = exam_review['review_text']
        user_details['review_date'] = exam_review['created_at']
        user_details['admin_job_field'] = exam_review['admin_job_field']
    else:
        user_details['has_review'] = False
    
    # Get exam responses with question text - including both personality and puzzle questions
    cursor.execute("""
        SELECT r.id, q.id as question_id, q.question_text, q.question_type, 
               r.response, r.attempts, r.score, r.created_at,
               q.question_data
        FROM exam_responses r
        JOIN exam_questions q ON r.question_id = q.id
        WHERE r.user_id = ?
        ORDER BY q.question_order
    """, (user_id,))
    
    responses = [dict(row) for row in cursor.fetchall()]
    
    # Process responses based on question type
    for response in responses:
        if response["question_type"] == "personality":
            # Map personality response values to text
            value = int(response["response"])
            if value == 1:
                response["response_text"] = "كاملاً مخالفم"
            elif value == 2:
                response["response_text"] = "مخالفم"
            elif value == 3:
                response["response_text"] = "خنثي"
            elif value == 4:
                response["response_text"] = "موافقم"
            elif value == 5:
                response["response_text"] = "كاملاً موافقم"
        else:  # puzzle
            # Parse question data
            if response["question_data"]:
                data = json.loads(response["question_data"])
                options = data.get("options", [])
                
                # Get selected option text
                try:
                    option_index = int(response["response"])
                    if isinstance(options, list):
                        if option_index < len(options):
                            if isinstance(options[option_index], dict):
                                response["response_text"] = options[option_index].get("text", options[option_index].get("value", ""))
                            else:
                                response["response_text"] = options[option_index]
                        else:
                            response["response_text"] = f"گزینه {option_index + 1}"
                    else:
                        response["response_text"] = response["response"]
                except (ValueError, IndexError):
                    response["response_text"] = response["response"]
                
                # Add score information
                if response["score"] is not None:
                    if response["score"] == 1.0:
                        response["score_text"] = "امتیاز کامل (1.0)"
                    elif response["score"] == 0.5:
                        response["score_text"] = "امتیاز نسبی (0.5)"
                    else:
                        response["score_text"] = "امتیاز صفر (0.0)"
                else:
                    response["score_text"] = "بدون امتیاز"
                
                # Add attempts information
                response["attempts_text"] = f"{response['attempts']} تلاش"
            else:
                response["response_text"] = response["response"]
                response["score_text"] = "نامشخص"
                response["attempts_text"] = "نامشخص"
    
    conn.close()
    
    return user_details, responses