# app/routers/exam.py (Unified approach)
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Dict, List, Optional, Any
import json

# Import functions
from app.database import (
    get_question_by_order, get_total_questions, save_exam_response, 
    mark_exam_completed, has_completed_exam, get_user_progress,
    has_user_answered_question, get_question_by_id
)
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
        from app.database import get_exam_review
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
    
    # Get user progress if they've started the exam
    progress = get_user_progress(current_user["id"])
    if progress > 0:
        # User has started but not completed - show resume option
        return templates.TemplateResponse(
            "exam_resume.html", 
            {
                "request": request, 
                "title": "ادامه آزمون",
                "user": current_user,
                "progress": progress,
                "total_questions": get_total_questions()
            }
        )
    
    # Fresh start - show intro page
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
    
    # Get user progress
    progress = get_user_progress(current_user["id"])
    
    # Get the question to display (either the first one or where they left off)
    question_order = progress + 1
    question = get_question_by_order(question_order)
    
    # If no question found, redirect to error page
    if not question:
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request, 
                "title": "خطا",
                "message": "سوالات آزمون در دسترس نیست. لطفاً با مدیر سیستم تماس بگیرید."
            }
        )
    
    total_questions = get_total_questions()
    
    # Determine template and context based on question type
    if question["question_type"] == "personality":
        return templates.TemplateResponse(
            "exam.html", 
            {
                "request": request, 
                "title": "آزمون شخصیت و هوش",
                "user": current_user,
                "question": question,
                "question_index": question_order,
                "total_questions": total_questions
            }
        )
    else:  # puzzle type
        return templates.TemplateResponse(
            "exam.html", 
            {
                "request": request, 
                "title": "آزمون شخصیت و هوش",
                "user": current_user,
                "question": question,
                "question_index": question_order,
                "total_questions": total_questions,
                "attempts_left": 2  # For puzzle questions, start with 2 attempts
            }
        )

@router.post("/exam/submit_answer")
async def submit_answer(
    request: Request,
    question_id: int = Form(...),
    response: str = Form(...),
    current_question_index: int = Form(...),
    attempts_left: Optional[int] = Form(None),  # Only for puzzle questions
    current_user: Dict = Depends(get_current_user)
):
    """
    Process answer submission for both personality and puzzle questions
    """
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Get the current question
    question = get_question_by_id(question_id)
    if not question:
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request, 
                "title": "خطا",
                "message": "سوال مورد نظر یافت نشد."
            }
        )
    
    total_questions = get_total_questions()
    
    # Handle personality and puzzle questions differently
    if question["question_type"] == "personality":
        # For personality questions, simply save the response
        save_exam_response(
            user_id=current_user["id"],
            question_id=question_id,
            response=response
        )
        
        # Continue to next question or finish the exam
        next_question_index = current_question_index + 1
        
        # Check if this was the last question
        if next_question_index > total_questions:
            # Mark the exam as completed
            mark_exam_completed(current_user["id"])
            
            # Redirect to thank you page
            return RedirectResponse(url="/exam/thank_you", status_code=status.HTTP_303_SEE_OTHER)
        
        # Get the next question
        next_question = get_question_by_order(next_question_index)
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        
        if is_ajax:
            # For AJAX requests, return HTML fragment and data as JSON
            if next_question["question_type"] == "personality":
                template_name = "partials/question_card.html"
                context = {
                    "question": next_question,
                    "question_index": next_question_index,
                    "total_questions": total_questions
                }
            else:  # puzzle
                template_name = "partials/puzzle_card.html"
                context = {
                    "question": next_question,
                    "question_index": next_question_index,
                    "total_questions": total_questions,
                    "attempts_left": 2  # Start with 2 attempts for puzzle
                }
            
            question_card_html = templates.get_template(template_name).render(context)
            
            progress_percentage = (next_question_index / total_questions) * 100
            
            return JSONResponse(content={
                "html": question_card_html,
                "question_index": next_question_index,
                "total_questions": total_questions,
                "progress": progress_percentage,
                "question_type": next_question["question_type"],
                "attempts_left": 2 if next_question["question_type"] == "puzzle" else None
            })
        else:
            # For regular form submissions, redirect to appropriate template
            if next_question["question_type"] == "personality":
                return templates.TemplateResponse(
                    "exam.html", 
                    {
                        "request": request, 
                        "title": "آزمون شخصیت و هوش",
                        "user": current_user,
                        "question": next_question,
                        "question_index": next_question_index,
                        "total_questions": total_questions
                    }
                )
            else:  # puzzle
                return templates.TemplateResponse(
                    "exam.html", 
                    {
                        "request": request, 
                        "title": "آزمون شخصیت و هوش",
                        "user": current_user,
                        "question": next_question,
                        "question_index": next_question_index,
                        "total_questions": total_questions,
                        "attempts_left": 2  # Start with 2 attempts for puzzle
                    }
                )
    
    else:  # Puzzle question
        # For puzzle questions, check if answer is correct
        if attempts_left is None:
            attempts_left = 2  # Default to 2 attempts if not provided
        
        attempts_left = int(attempts_left)
        attempts_made = 3 - attempts_left  # We start with 2 attempts left, so this is either 1 or 2
        
        # Check if the answer is correct
        correct_answer = question["question_data"]["correct_answer"]
        is_correct = response == correct_answer
        
        # Calculate score based on attempts
        score = 0.0
        if is_correct:
            if attempts_made == 1:  # First try
                score = 1.0
            elif attempts_made == 2:  # Second try
                score = 0.5
        
        # If correct or no attempts left, save the final answer and move on
        should_move_to_next = is_correct or attempts_left <= 1
        
        if should_move_to_next:
            # Save the response with final score
            save_exam_response(
                user_id=current_user["id"],
                question_id=question_id,
                response=response,
                attempts=attempts_made,
                score=score
            )
            
            # Check if this was the last question
            if current_question_index >= total_questions:
                # Mark the exam as completed
                mark_exam_completed(current_user["id"])
                
                # Check if this is an AJAX request
                is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
                if is_ajax:
                    return JSONResponse(content={
                        "redirect": "/exam/thank_you"
                    })
                else:
                    # Regular form submission
                    return RedirectResponse(url="/exam/thank_you", status_code=status.HTTP_303_SEE_OTHER)
            
            # Move to the next question
            next_question_index = current_question_index + 1
            next_question = get_question_by_order(next_question_index)
            
            # Check if this is an AJAX request
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            
            if is_ajax:
                # For AJAX requests, return HTML fragment and data as JSON
                if next_question["question_type"] == "personality":
                    template_name = "partials/question_card.html"
                    context = {
                        "question": next_question,
                        "question_index": next_question_index,
                        "total_questions": total_questions
                    }
                else:  # puzzle
                    template_name = "partials/puzzle_card.html"
                    context = {
                        "question": next_question,
                        "question_index": next_question_index,
                        "total_questions": total_questions,
                        "attempts_left": 2  # Reset attempts for new puzzle
                    }
                
                question_card_html = templates.get_template(template_name).render(context)
                
                progress_percentage = (next_question_index / total_questions) * 100
                
                return JSONResponse(content={
                    "html": question_card_html,
                    "question_index": next_question_index,
                    "total_questions": total_questions,
                    "progress": progress_percentage,
                    "question_type": next_question["question_type"],
                    "attempts_left": 2 if next_question["question_type"] == "puzzle" else None
                })
            else:
                # For regular form submissions, redirect to appropriate template
                if next_question["question_type"] == "personality":
                    return templates.TemplateResponse(
                        "exam.html", 
                        {
                            "request": request, 
                            "title": "آزمون شخصیت و هوش",
                            "user": current_user,
                            "question": next_question,
                            "question_index": next_question_index,
                            "total_questions": total_questions
                        }
                    )
                else:  # puzzle
                    return templates.TemplateResponse(
                        "exam.html", 
                        {
                            "request": request, 
                            "title": "آزمون شخصیت و هوش",
                            "user": current_user,
                            "question": next_question,
                            "question_index": next_question_index,
                            "total_questions": total_questions,
                            "attempts_left": 2  # Reset attempts for new puzzle
                        }
                    )
        else:
            # Incorrect answer but still has attempts left - stay on same puzzle
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            
            # Reduce attempts left
            attempts_left -= 1
            
            if is_ajax:
                # For AJAX requests, return the result with feedback
                return JSONResponse(content={
                    "is_correct": False,
                    "attempts_left": attempts_left,
                    "feedback": "پاسخ اشتباه است. لطفاً دوباره تلاش کنید."
                })
            else:
                # For regular form submissions
                return templates.TemplateResponse(
                    "exam.html", 
                    {
                        "request": request, 
                        "title": "آزمون شخصیت و هوش",
                        "user": current_user,
                        "question": question,
                        "question_index": current_question_index,
                        "total_questions": total_questions,
                        "attempts_left": attempts_left,
                        "feedback": "پاسخ اشتباه است. لطفاً دوباره تلاش کنید."
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

@router.get("/exam/resume", response_class=HTMLResponse)
async def resume_exam(request: Request, current_user: Dict = Depends(get_current_user)):
    """
    Resume the exam from where the user left off
    """
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Check if user has already completed the exam
    if has_completed_exam(current_user["id"]):
        return RedirectResponse(url="/exam")
    
    # Get user progress
    progress = get_user_progress(current_user["id"])
    
    # Get the next question to display
    question_order = progress + 1
    question = get_question_by_order(question_order)
    
    # If no question found or all questions are answered, redirect to thank you page
    if not question or question_order > get_total_questions():
        # Mark the exam as completed if all questions answered
        if question_order > get_total_questions():
            mark_exam_completed(current_user["id"])
        
        return RedirectResponse(url="/exam/thank_you")
    
    total_questions = get_total_questions()
    
    # Determine template and context based on question type
    if question["question_type"] == "personality":
        return templates.TemplateResponse(
            "exam.html", 
            {
                "request": request, 
                "title": "آزمون شخصیت و هوش",
                "user": current_user,
                "question": question,
                "question_index": question_order,
                "total_questions": total_questions
            }
        )
    else:  # puzzle type
        return templates.TemplateResponse(
            "exam.html", 
            {
                "request": request, 
                "title": "آزمون شخصیت و هوش",
                "user": current_user,
                "question": question,
                "question_index": question_order,
                "total_questions": total_questions,
                "attempts_left": 2  # For puzzle questions, start with 2 attempts
            }
        )