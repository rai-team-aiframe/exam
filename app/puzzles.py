# app/puzzles.py
import sqlite3
from typing import List, Dict, Any, Optional
import json
from .database import get_db_connection

def import_puzzle_questions():
    """
    Import puzzle questions into the database.
    This function should be called during app startup.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if puzzle questions are already imported
    cursor.execute("SELECT COUNT(*) FROM puzzle_questions")
    count = cursor.fetchone()[0]
    
    # Only import if no questions exist
    if count == 0:
        # Sample puzzle questions with data
        puzzle_questions = [
            {
                "question_text": "کدام مسیر انسان را به خانه می‌رساند؟",
                "puzzle_type": "path_finding",
                "puzzle_data": json.dumps({
                    "grid": [
                        [0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 1, 1, 1, 0],
                        [0, 1, 0, 0, 0, 0, 1, 0],
                        [0, 1, 0, 1, 1, 0, 1, 0],
                        [0, 1, 0, 1, 1, 0, 1, 0],
                        [0, 1, 0, 0, 0, 0, 1, 0],
                        [0, 1, 1, 1, 1, 1, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    "start": [1, 1],
                    "end": [6, 6],
                    "options": [
                        "راه راست، پایین، راست، بالا، راست",
                        "راه راست، پایین، راست، بالا، پایین، راست",
                        "راه پایین، راست، پایین، راست، بالا، راست",
                        "راه پایین، راست، بالا، راست، پایین، راست"
                    ]
                }),
                "correct_answer": "3"  # Option index (0-based)
            },
            {
                "question_text": "کدام قطعه جای خالی را پر می‌کند؟",
                "puzzle_type": "pattern_match",
                "puzzle_data": json.dumps({
                    "main_pattern": [
                        [1, 2, 3],
                        [4, 0, 6],
                        [7, 8, 9]
                    ],
                    "options": [
                        {"value": 5, "text": "دایره"},
                        {"value": 10, "text": "مثلث"},
                        {"value": 15, "text": "مربع"},
                        {"value": 20, "text": "ستاره"}
                    ]
                }),
                "correct_answer": "0"  # Option index (0-based)
            },
            {
                "question_text": "کدام رنگ الگوی داده شده را تکمیل می‌کند؟",
                "puzzle_type": "color_pattern",
                "puzzle_data": json.dumps({
                    "pattern": ["red", "blue", "green", "red", "blue", "?"],
                    "options": [
                        {"value": "green", "text": "سبز"},
                        {"value": "yellow", "text": "زرد"},
                        {"value": "blue", "text": "آبی"},
                        {"value": "red", "text": "قرمز"}
                    ]
                }),
                "correct_answer": "0"  # Option index (0-based)
            },
            {
                "question_text": "کدام تصویر خانه را نمایش می‌دهد؟",
                "puzzle_type": "image_recognition",
                "puzzle_data": json.dumps({
                    "images": [
                        "building.svg",
                        "house.svg",
                        "tower.svg",
                        "cabin.svg"
                    ]
                }),
                "correct_answer": "1"  # Option index (0-based)
            },
            {
                "question_text": "کدام عدد در دنباله زیر باید قرار بگیرد؟ 2, 4, 8, 16, ?",
                "puzzle_type": "number_sequence",
                "puzzle_data": json.dumps({
                    "sequence": [2, 4, 8, 16],
                    "options": [
                        {"value": 24, "text": "24"},
                        {"value": 32, "text": "32"},
                        {"value": 30, "text": "30"},
                        {"value": 18, "text": "18"}
                    ]
                }),
                "correct_answer": "1"  # Option index (0-based)
            },
            {
                "question_text": "با کدام حرکت میتوانید مهره سیاه را به گوشه برسانید؟",
                "puzzle_type": "chess_move",
                "puzzle_data": json.dumps({
                    "board": [
                        ["", "", "", "", "", "", "", ""],
                        ["", "", "", "", "", "", "", ""],
                        ["", "", "", "", "", "", "", ""],
                        ["", "", "", "K", "", "", "", ""],
                        ["", "", "", "", "P", "", "", ""],
                        ["", "", "", "", "", "", "", ""],
                        ["", "", "", "", "", "", "", ""],
                        ["", "", "", "", "", "", "", ""]
                    ],
                    "options": [
                        {"value": "e4-e5", "text": "پیاده به جلو"},
                        {"value": "e4-d5", "text": "پیاده به چپ"},
                        {"value": "e4-f5", "text": "پیاده به راست"},
                        {"value": "d3-e4", "text": "شاه به جلو"}
                    ]
                }),
                "correct_answer": "2"  # Option index (0-based)
            },
            {
                "question_text": "کدام گزینه دنباله حروف را کامل می‌کند؟ A, C, E, G, ?",
                "puzzle_type": "letter_sequence",
                "puzzle_data": json.dumps({
                    "sequence": ["A", "C", "E", "G"],
                    "options": [
                        {"value": "I", "text": "I"},
                        {"value": "J", "text": "J"},
                        {"value": "H", "text": "H"},
                        {"value": "K", "text": "K"}
                    ]
                }),
                "correct_answer": "0"  # Option index (0-based)
            },
            {
                "question_text": "کدام شکل با الگوی داده شده مطابقت دارد؟",
                "puzzle_type": "shape_pattern",
                "puzzle_data": json.dumps({
                    "pattern": ["circle", "square", "triangle", "circle", "square", "?"],
                    "options": [
                        {"value": "triangle", "text": "مثلث"},
                        {"value": "square", "text": "مربع"},
                        {"value": "circle", "text": "دایره"},
                        {"value": "pentagon", "text": "پنج ضلعی"}
                    ]
                }),
                "correct_answer": "0"  # Option index (0-based)
            },
            {
                "question_text": "کدام تصویر با بقیه متفاوت است؟",
                "puzzle_type": "odd_one_out",
                "puzzle_data": json.dumps({
                    "options": [
                        {"value": "apple.svg", "text": "سیب"},
                        {"value": "orange.svg", "text": "پرتقال"},
                        {"value": "banana.svg", "text": "موز"},
                        {"value": "carrot.svg", "text": "هویج"}
                    ]
                }),
                "correct_answer": "3"  # Option index (0-based)
            },
            {
                "question_text": "کدام قطعه پازل تصویر را کامل می‌کند؟",
                "puzzle_type": "jigsaw",
                "puzzle_data": json.dumps({
                    "image": "puzzle_image.svg",
                    "missing_piece": [2, 2],
                    "options": [
                        "piece1.svg",
                        "piece2.svg",
                        "piece3.svg",
                        "piece4.svg"
                    ]
                }),
                "correct_answer": "2"  # Option index (0-based)
            },
            {
                "question_text": "با توجه به الگوی اعداد، عدد بعدی کدام است؟ 3, 6, 12, 24, ?",
                "puzzle_type": "number_sequence",
                "puzzle_data": json.dumps({
                    "sequence": [3, 6, 12, 24],
                    "options": [
                        {"value": 36, "text": "36"},
                        {"value": 48, "text": "48"},
                        {"value": 30, "text": "30"},
                        {"value": 42, "text": "42"}
                    ]
                }),
                "correct_answer": "1"  # Option index (0-based)
            },
            {
                "question_text": "کدام تصویر منطقی الگوی داده شده را ادامه می‌دهد؟",
                "puzzle_type": "logical_sequence",
                "puzzle_data": json.dumps({
                    "sequence": [
                        "sequence1.svg",
                        "sequence2.svg",
                        "sequence3.svg"
                    ],
                    "options": [
                        "option1.svg",
                        "option2.svg",
                        "option3.svg",
                        "option4.svg"
                    ]
                }),
                "correct_answer": "2"  # Option index (0-based)
            },
            {
                "question_text": "کدام عبارت با بقیه متفاوت است؟",
                "puzzle_type": "verbal_odd_one_out",
                "puzzle_data": json.dumps({
                    "options": [
                        {"value": "dog", "text": "سگ"},
                        {"value": "cat", "text": "گربه"},
                        {"value": "elephant", "text": "فیل"},
                        {"value": "table", "text": "میز"}
                    ]
                }),
                "correct_answer": "3"  # Option index (0-based)
            },
            {
                "question_text": "کدام کلید را باید فشار دهید تا قفل باز شود؟",
                "puzzle_type": "lock_puzzle",
                "puzzle_data": json.dumps({
                    "lock_pattern": [3, 5, 7, "?"],
                    "options": [
                        {"value": 9, "text": "9"},
                        {"value": 11, "text": "11"},
                        {"value": 8, "text": "8"},
                        {"value": 10, "text": "10"}
                    ]
                }),
                "correct_answer": "1"  # Option index (0-based)
            },
            {
                "question_text": "کدام مسیر شما را از هزارتو خارج می‌کند؟",
                "puzzle_type": "maze",
                "puzzle_data": json.dumps({
                    "maze": [
                        [0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 1, 1, 0],
                        [0, 1, 0, 0, 0, 1, 0],
                        [0, 1, 1, 1, 0, 1, 0],
                        [0, 0, 0, 1, 0, 1, 0],
                        [0, 1, 1, 1, 0, 1, 0],
                        [0, 1, 0, 0, 0, 1, 0],
                        [0, 1, 1, 1, 1, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0]
                    ],
                    "start": [1, 1],
                    "end": [7, 5],
                    "options": [
                        "راه راست، پایین، راست، پایین، راست، پایین",
                        "راه پایین، راست، پایین، پایین، راست، پایین",
                        "راه پایین، پایین، راست، پایین، راست، پایین",
                        "راه راست، پایین، راست، پایین، راست، راست، پایین"
                    ]
                }),
                "correct_answer": "0"  # Option index (0-based)
            }
        ]
        
        # Insert puzzle questions
        for puzzle in puzzle_questions:
            cursor.execute(
                "INSERT INTO puzzle_questions (question_text, puzzle_type, puzzle_data, correct_answer) VALUES (?, ?, ?, ?)",
                (puzzle["question_text"], puzzle["puzzle_type"], puzzle["puzzle_data"], puzzle["correct_answer"])
            )
        
        print(f"Imported {len(puzzle_questions)} puzzle questions.")
    
    conn.commit()
    conn.close()

def get_puzzle_by_id(puzzle_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific puzzle question by ID
    
    Args:
        puzzle_id (int): The ID of the puzzle to retrieve
        
    Returns:
        Dict[str, Any]: The puzzle data or None if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM puzzle_questions WHERE id = ?", (puzzle_id,))
    puzzle = cursor.fetchone()
    
    conn.close()
    
    if puzzle:
        result = dict(puzzle)
        # Parse puzzle_data from JSON string to Python dictionary
        result["puzzle_data"] = json.loads(result["puzzle_data"])
        return result
    
    return None

def get_all_puzzles() -> List[Dict[str, Any]]:
    """
    Retrieve all puzzle questions
    
    Returns:
        List[Dict[str, Any]]: List of all puzzle questions
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM puzzle_questions")
    puzzles = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Parse puzzle_data for each puzzle
    for puzzle in puzzles:
        puzzle["puzzle_data"] = json.loads(puzzle["puzzle_data"])
    
    return puzzles

def save_puzzle_response(user_id: int, puzzle_id: int, response: str, attempts: int, score: float) -> int:
    """
    Save a user's response to a puzzle
    
    Args:
        user_id (int): The user ID
        puzzle_id (int): The puzzle ID
        response (str): The user's response (option index)
        attempts (int): Number of attempts made (1 or 2)
        score (float): Score awarded (1.0, 0.5, or 0.0)
        
    Returns:
        int: The response ID
    """
    from datetime import datetime
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    
    cursor.execute('''
    INSERT INTO puzzle_responses (user_id, puzzle_id, response, attempts, score, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, puzzle_id, response, attempts, score, created_at))
    
    response_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return response_id

def mark_puzzle_section_completed(user_id: int) -> None:
    """
    Mark that a user has completed the puzzle section
    
    Args:
        user_id (int): The user ID
    """
    from datetime import datetime
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    completion_date = datetime.now().isoformat()
    
    # Check if user has an entry in completed_exams
    cursor.execute("SELECT id FROM completed_exams WHERE user_id = ?", (user_id,))
    existing_entry = cursor.fetchone()
    
    if existing_entry:
        # Update existing entry
        cursor.execute('''
        UPDATE completed_exams 
        SET puzzle_completed = 1, completion_date = ?
        WHERE user_id = ?
        ''', (completion_date, user_id))
    else:
        # Create new entry
        cursor.execute('''
        INSERT INTO completed_exams (user_id, puzzle_completed, completion_date)
        VALUES (?, 1, ?)
        ''', (user_id, completion_date))
    
    conn.commit()
    conn.close()

def has_completed_puzzle_section(user_id: int) -> bool:
    """
    Check if a user has already completed the puzzle section
    
    Args:
        user_id (int): The user ID
        
    Returns:
        bool: True if the user has completed the puzzle section
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT puzzle_completed FROM completed_exams WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result is not None and result["puzzle_completed"] == 1

def calculate_puzzle_score(user_id: int) -> Dict[str, Any]:
    """
    Calculate the puzzle test score for a user
    
    Args:
        user_id (int): The user ID
        
    Returns:
        Dict[str, Any]: The calculated scores
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all puzzle responses for the user
    cursor.execute("""
        SELECT q.id, q.question_text, q.puzzle_type, r.response, r.attempts, r.score
        FROM puzzle_responses r
        JOIN puzzle_questions q ON r.puzzle_id = q.id
        WHERE r.user_id = ?
        ORDER BY q.id
    """, (user_id,))
    
    responses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    total_puzzles = len(responses)
    if total_puzzles == 0:
        return {
            "total_score": 0,
            "average_score": 0,
            "total_puzzles": 0,
            "completed_puzzles": 0,
            "perfect_score_puzzles": 0,
            "partial_score_puzzles": 0,
            "failed_puzzles": 0
        }
    
    total_score = sum(response["score"] for response in responses)
    average_score = total_score / total_puzzles
    
    perfect_score_puzzles = sum(1 for response in responses if response["score"] == 1.0)
    partial_score_puzzles = sum(1 for response in responses if response["score"] == 0.5)
    failed_puzzles = sum(1 for response in responses if response["score"] == 0.0)
    
    return {
        "total_score": total_score,
        "average_score": average_score,
        "total_puzzles": total_puzzles,
        "completed_puzzles": total_puzzles,
        "perfect_score_puzzles": perfect_score_puzzles,
        "partial_score_puzzles": partial_score_puzzles,
        "failed_puzzles": failed_puzzles
    }

def get_puzzle_responses(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all puzzle responses for a user with question details
    
    Args:
        user_id (int): The user ID
        
    Returns:
        List[Dict[str, Any]]: List of responses with question details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.id, q.id as puzzle_id, q.question_text, q.puzzle_type, 
               r.response, r.attempts, r.score, r.created_at
        FROM puzzle_responses r
        JOIN puzzle_questions q ON r.puzzle_id = q.id
        WHERE r.user_id = ?
        ORDER BY q.id
    """, (user_id,))
    
    responses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return responses