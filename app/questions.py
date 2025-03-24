# app/questions.py
import sqlite3
from typing import List, Dict, Any
from .database import get_db_connection

def import_questions_from_list(questions: List[str]) -> None:
    """
    Imports personality test questions into the database from a list.
    
    Args:
        questions (List[str]): A list of question strings
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the questions table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personality_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL
        )
    ''')
    
    # Check if questions are already imported
    cursor.execute("SELECT COUNT(*) FROM personality_questions")
    count = cursor.fetchone()[0]
    
    # Only import if no questions exist
    if count == 0:
        # Insert questions
        for question in questions:
            cursor.execute(
                "INSERT INTO personality_questions (question_text) VALUES (?)",
                (question,)
            )
    
    conn.commit()
    conn.close()


def get_question_by_id(question_id: int) -> Dict[str, Any]:
    """
    Retrieve a specific question by ID
    
    Args:
        question_id (int): The ID of the question to retrieve
        
    Returns:
        Dict[str, Any]: The question data
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM personality_questions WHERE id = ?", (question_id,))
    question = cursor.fetchone()
    
    conn.close()
    
    if question:
        return dict(question)
    
    return None


def get_all_questions() -> List[Dict[str, Any]]:
    """
    Retrieve all questions from the database
    
    Returns:
        List[Dict[str, Any]]: List of all questions
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM personality_questions")
    questions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return questions


def calculate_score(user_id: int) -> Dict[str, Any]:
    """
    Calculate the personality test score for a user
    
    Args:
        user_id (int): The user ID
        
    Returns:
        Dict[str, Any]: The calculated scores
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all responses for the user
    cursor.execute("""
        SELECT q.id, q.question_text, r.response 
        FROM exam_responses r
        JOIN personality_questions q ON r.question_id = q.id
        WHERE r.user_id = ?
        ORDER BY q.id
    """, (user_id,))
    
    responses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Here you would implement your scoring algorithm
    # This is a placeholder for the actual scoring logic
    # You might want to categorize questions and calculate scores for different traits
    
    scores = {
        "openness": 0,
        "conscientiousness": 0,
        "extraversion": 0,
        "agreeableness": 0,
        "neuroticism": 0
    }
    
    # Example simple scoring (just a placeholder)
    for response in responses:
        question_id = response["id"]
        answer_value = response["response"]
        
        # Map questions to traits (this would be based on your test design)
        # Example mapping logic - replace with your actual mapping
        if question_id % 5 == 0:
            scores["openness"] += answer_value
        elif question_id % 5 == 1:
            scores["conscientiousness"] += answer_value
        elif question_id % 5 == 2:
            scores["extraversion"] += answer_value
        elif question_id % 5 == 3:
            scores["agreeableness"] += answer_value
        elif question_id % 5 == 4:
            scores["neuroticism"] += answer_value
    
    # Normalize scores (example)
    for trait in scores:
        # Assuming 12 questions per trait with values 1-5
        scores[trait] = round((scores[trait] / 60) * 100, 2)
    
    return scores