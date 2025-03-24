# app/routers/home.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Initialize router
router = APIRouter(tags=["home"])

# Set up templates
templates = Jinja2Templates(directory="templates")

@router.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    """
    Render the home page
    """
    return templates.TemplateResponse(
        "home.html", 
        {"request": request, "title": "صفحه اصلی"}
    )