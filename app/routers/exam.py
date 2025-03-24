# app/routers/exam.py
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Dict, List, Optional, Any
import json

# Use absolute imports
from app.database import get_all_questions, save_exam_response, mark_exam_completed, has_completed_exam, get_exam_review
from app.routers.auth import get_current_user
from app.date_utils import format_date_shamsi

# Initialize router
router = APIRouter(tags=["exam"])

# Set up templates
templates = Jinja2Templates(directory="templates")

# Add date formatting function to Jinja environment
templates.env.globals["format_date_shamsi"] = format_date_shamsi

@router.get("/exam", response_class=HTMLResponse)
async def exam_page(request: Request, current_user: Dict = Depends(get_current_user)):
    """
    Render the exam start page or redirect to login if not authenticated
    """
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Check if user has already completed the exam
    if has_completed_exam(current_user["id"]):
        # Check if there's a review available
        review = get_exam_review(current_user["id"])
        
        if review:
            # Show the review page
            return templates.TemplateResponse(
                "exam_review.html", 
                {
                    "request": request, 
                    "title": "نتیجه بررسی آزمون",
                    "user": current_user,
                    "review": review
                }
            )
        else:
            # Show the already completed page
            return templates.TemplateResponse(
                "already_completed.html", 
                {
                    "request": request, 
                    "title": "آزمون قبلاً تکمیل شده",
                    "user": current_user
                }
            )
    
    return templates.TemplateResponse(
        "exam_intro.html", 
        {
            "request": request, 
            "title": "شروع آزمون",
            "user": current_user
        }
    )

@router.get("/exam/start", response_class=HTMLResponse)
async def start_exam(request: Request, current_user: Dict = Depends(get_current_user)):
    """
    Start the exam and load the first question
    """
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Check if user has already completed the exam
    if has_completed_exam(current_user["id"]):
        return RedirectResponse(url="/exam")
    
    # Get all questions
    questions = get_all_questions()
    
    # If no questions in DB, redirect to error page
    if not questions:
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request, 
                "title": "خطا",
                "message": "سوالات آزمون در دسترس نیست. لطفاً با مدیر سیستم تماس بگیرید."
            }
        )
    
    # Start with the first question
    current_question = questions[0]
    total_questions = len(questions)
    
    return templates.TemplateResponse(
        "exam.html", 
        {
            "request": request, 
            "title": "آزمون شخصیت",
            "user": current_user,
            "question": current_question,
            "question_index": 1,
            "total_questions": total_questions
        }
    )

@router.post("/exam/submit_answer", response_class=HTMLResponse)
async def submit_answer(
    request: Request,
    question_id: int = Form(...),
    response: int = Form(...),
    current_question_index: int = Form(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Save the user's answer and move to the next question
    """
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Save the response
    save_exam_response(
        user_id=current_user["id"],
        question_id=question_id,
        response=response
    )
    
    # Get all questions
    questions = get_all_questions()
    total_questions = len(questions)
    
    # Check if this was the last question
    if current_question_index >= total_questions:
        # Mark the exam as completed
        mark_exam_completed(current_user["id"])
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if is_ajax:
            return RedirectResponse(url="/exam/thank_you", status_code=status.HTTP_303_SEE_OTHER)
        else:
            # Regular form submission
            return RedirectResponse(url="/exam/thank_you", status_code=status.HTTP_303_SEE_OTHER)
    
    # Move to the next question
    next_question_index = current_question_index
    next_question = questions[next_question_index]
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    
    if is_ajax:
        # For AJAX requests, return HTML fragment and data as JSON
        question_card_html = templates.get_template("partials/question_card.html").render(
            {
                "question": next_question,
                "question_index": next_question_index + 1,
                "total_questions": total_questions
            }
        )
        
        progress_percentage = ((next_question_index + 1) / total_questions) * 100
        
        return JSONResponse(content={
            "html": question_card_html,
            "question_index": next_question_index + 1,
            "total_questions": total_questions,
            "progress": progress_percentage
        })
    else:
        # For regular form submissions
        return templates.TemplateResponse(
            "exam.html", 
            {
                "request": request, 
                "title": "آزمون شخصیت",
                "user": current_user,
                "question": next_question,
                "question_index": next_question_index + 1,
                "total_questions": total_questions
            }
        )

@router.get("/exam/thank_you", response_class=HTMLResponse)
async def thank_you_page(request: Request, current_user: Dict = Depends(get_current_user)):
    """
    Show thank you page after completing the exam
    """
    if not current_user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "thank_you.html", 
        {
            "request": request, 
            "title": "با تشکر از شما",
            "user": current_user
        }
    )