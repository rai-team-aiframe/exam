# app/database.py
import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status


def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect('online_exam.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        id_number TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        birth_date TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Create personality_questions table (if not already imported)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS personality_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL
    )
    ''')
    
    # Create exam_responses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        response INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (question_id) REFERENCES personality_questions (id)
    )
    ''')
    
    # Create a completed_exams table to track who has completed the exam
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS completed_exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        completion_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()


def init_db_updates():
    """Add new tables needed for exam review and retake features"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create exam_reviews table to store admin reviews
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        review_text TEXT NOT NULL,
        admin_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (admin_id) REFERENCES admins (id)
    )
    ''')
    
    conn.commit()
    conn.close()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return dict(user)
    return None


def get_user_by_id_number(id_number: str) -> Optional[Dict[str, Any]]:
    """Get user by ID number"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id_number = ?", (id_number,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return dict(user)
    return None


def create_user(username: str, password: str, id_number: str, 
                first_name: str, last_name: str, birth_date: str, 
                phone_number: str) -> int:
    """Create a new user in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First check if the id_number already exists
    if get_user_by_id_number(id_number):
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="این کد ملی قبلاً در سیستم ثبت شده است."
        )
    
    created_at = datetime.now().isoformat()
    
    try:
        cursor.execute('''
        INSERT INTO users (username, password, id_number, first_name, last_name, birth_date, phone_number, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, id_number, first_name, last_name, birth_date, phone_number, created_at))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    except sqlite3.IntegrityError as e:
        conn.close()
        
        if "users.username" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="این نام کاربری قبلاً استفاده شده است."
            )
        elif "users.id_number" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="این کد ملی قبلاً در سیستم ثبت شده است."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="خطا در ثبت اطلاعات. لطفاً مجدداً تلاش کنید."
            )


def get_all_questions() -> List[Dict[str, Any]]:
    """Get all personality questions from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM personality_questions")
    questions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return questions


def save_exam_response(user_id: int, question_id: int, response: int) -> int:
    """Save a user's response to a question"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    
    cursor.execute('''
    INSERT INTO exam_responses (user_id, question_id, response, created_at)
    VALUES (?, ?, ?, ?)
    ''', (user_id, question_id, response, created_at))
    
    response_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return response_id


def mark_exam_completed(user_id: int) -> None:
    """Mark that a user has completed the exam"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    completion_date = datetime.now().isoformat()
    
    cursor.execute('''
    INSERT OR REPLACE INTO completed_exams (user_id, completion_date)
    VALUES (?, ?)
    ''', (user_id, completion_date))
    
    conn.commit()
    conn.close()


def has_completed_exam(user_id: int) -> bool:
    """Check if a user has already completed the exam"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM completed_exams WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None


def mark_exam_reviewed(user_id: int, admin_id: int, review_text: str) -> int:
    """
    Mark a user's exam as reviewed and store the review text
    
    Args:
        user_id: The ID of the user whose exam is being reviewed
        admin_id: The ID of the admin who is reviewing the exam
        review_text: The review text to be shown to the user
        
    Returns:
        review_id: The ID of the created review
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    
    # First, check if a review already exists for this user
    cursor.execute("SELECT id FROM exam_reviews WHERE user_id = ?", (user_id,))
    existing_review = cursor.fetchone()
    
    if existing_review:
        # Update existing review
        cursor.execute('''
        UPDATE exam_reviews 
        SET review_text = ?, admin_id = ?, created_at = ?
        WHERE user_id = ?
        ''', (review_text, admin_id, created_at, user_id))
        review_id = existing_review[0]
    else:
        # Create new review
        cursor.execute('''
        INSERT INTO exam_reviews (user_id, review_text, admin_id, created_at)
        VALUES (?, ?, ?, ?)
        ''', (user_id, review_text, admin_id, created_at))
        review_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return review_id


def get_exam_review(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the review for a user's exam
    
    Args:
        user_id: The ID of the user whose review is being retrieved
        
    Returns:
        The review data or None if no review exists
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if admin_profiles table exists in the admin database
    cursor.execute('''
    SELECT name FROM sqlite_master WHERE type='table' AND name='admin_profiles'
    ''')
    profiles_table_exists = cursor.fetchone() is not None
    
    if profiles_table_exists:
        # Get exam review with admin job field
        cursor.execute('''
        SELECT er.*, a.username as admin_username, ap.job_field as admin_job_field
        FROM exam_reviews er
        JOIN admins a ON er.admin_id = a.id
        LEFT JOIN admin_profiles ap ON a.id = ap.admin_id
        WHERE er.user_id = ?
        ''', (user_id,))
    else:
        # Get exam review without profile data
        cursor.execute('''
        SELECT er.*, a.username as admin_username, NULL as admin_job_field
        FROM exam_reviews er
        JOIN admins a ON er.admin_id = a.id
        WHERE er.user_id = ?
        ''', (user_id,))
    
    review = cursor.fetchone()
    
    conn.close()
    
    if review:
        return dict(review)
    return None


def reset_user_exam(user_id: int) -> bool:
    """
    Reset a user's exam by deleting all their responses and completed_exams record
    
    Args:
        user_id: The ID of the user whose exam is being reset
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete all responses
        cursor.execute("DELETE FROM exam_responses WHERE user_id = ?", (user_id,))
        
        # Delete completed_exams record
        cursor.execute("DELETE FROM completed_exams WHERE user_id = ?", (user_id,))
        
        # Delete any reviews
        cursor.execute("DELETE FROM exam_reviews WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error resetting user exam: {e}")
        return False