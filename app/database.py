# app/database.py
import sqlite3
import os
import json
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
    
    # Create exam_questions table with type field
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        question_type TEXT NOT NULL,  -- 'personality' or 'puzzle'
        question_data TEXT,           -- JSON data for puzzle questions
        question_order INTEGER NOT NULL
    )
    ''')
    
    # Create exam_responses table for all question types
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        response TEXT NOT NULL,
        attempts INTEGER DEFAULT 1,
        score REAL DEFAULT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (question_id) REFERENCES exam_questions (id)
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
    
    # Create old personality_questions table for backwards compatibility
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS personality_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL
    )
    ''')
    
    # Create old exam_responses table for backwards compatibility
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_responses_old (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        response INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (question_id) REFERENCES personality_questions (id)
    )
    ''')

    conn.commit()
    conn.close()


def init_db_updates():
    """Add new tables and columns needed for exams"""
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
    
    # Add missing columns to exam_responses if they don't exist
    # First, check if the attempts column exists
    try:
        cursor.execute("SELECT attempts FROM exam_responses LIMIT 1")
    except sqlite3.OperationalError:
        # The column doesn't exist, so add it
        cursor.execute("ALTER TABLE exam_responses ADD COLUMN attempts INTEGER DEFAULT 1")
        print("Added 'attempts' column to exam_responses table")
    
    # Now check if the score column exists
    try:
        cursor.execute("SELECT score FROM exam_responses LIMIT 1")
    except sqlite3.OperationalError:
        # The column doesn't exist, so add it
        cursor.execute("ALTER TABLE exam_responses ADD COLUMN score REAL DEFAULT NULL")
        print("Added 'score' column to exam_responses table")
    
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


def import_all_questions():
    """Import both personality and puzzle questions into the exam_questions table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if questions are already imported
    cursor.execute("SELECT COUNT(*) FROM exam_questions")
    count = cursor.fetchone()[0]
    
    # Only import if no questions exist
    if count == 0:
        # First import personality questions (first 60 questions)
        personality_questions = [
            "1- من اصولا شخص نگراني نيستم.",
            "2- دوست دارم هميشه افراد زيادي دور و برم باشند.",
            "3- دوست ندارم وقتم را با خيال پردازي تلف كنم.",
            "4- سعي ميكنم در مقابل همه مودب باشم.",
            "5- وسايل متعلق به خود را تميز و مرتب نگاه مي دارم.",
            "6- اغلب خود را كمتر از ديگران حس مي كنم.",
            "7- زود به خنده مي افتم.",
            "8- هنگامي كه راه درست، كاري را پيدا كنم،آن روش را هميشه در آن مورد تكرار مي كنم.",
            "9- اغلب با فاميل و همكارانم بگو مگو دارم.",
            "10-به خوبي مي توانم كارهايم را طوري تنظيم كنم كه درست سر زمان تعيين شده انجام شوند.",
            "11- هنگامي كه تحت فشارهاي روحي زيادي هستم، گاه احساس مي كنم دارم خرد مي شوم.",
            "12- خودم را فرد خيلي سر حال و سر زنده اي نمي دانم.",
            "13- نقش هاي موجود در پديده هاي هنري و طبيعت مرا مبهوت مي كند.",
            "14- بعضي مردم فكر مي كنند كه من نشخصي خود خواه و خود محورم.",
            "15- فرد خيلي مرتب و منظمي نيستم.",
            "16- به ندرت احساس تنهايي و غم مي كنم.",
            "17- واقعا از صحبت كردن با ديگران لذت مي برم.",
            "18- فكر مي كنم گوش دادن دانشجويان به مطالب متناقض فقط به سردرگمي و گمراهي آن ها منجر خواهد شد.",
            "19- همكاري را بر رقابت با ديگران ترجيح مي دهم.",
            "20- سعي مي كنم همه كارهايم را با احساس مسوليت انجام دهم.",
            "21- اغلب احساس عصبي بودن و تنش مي كنم.",
            "22- هميشه براي كار آماده ام.",
            "23- شعر تقريبا اثري بر من ندارد.",
            "24- نسبت به قصد و نيت ديگران حساس  مشكوك هستم.",
            "25- داراي هدف روشني هستم و براي رسيدن به آن طبق برنامه كار ميكنم.",
            "26- گاهي كاملا احساس بي ارزشي مي كنم.",
            "27- غالباً ترجيح مي دهم كار ها را به تنهايي انجام دهم.",
            "28- اغلب غذاهاي جديد و خارجي را امتحان مي كنم.",
            "29- معتقدم اگر به مردم اجازه  دهيد، اكثر آن ها از شما سوء استفاده مي كنند.",
            "30- قبل از شروع هر كاري وقت زيادي را تلف مي كنم.",
            "31- به ندرت احساس اضطراب يا ترس مي كنم.",
            "32- اغلب احساس مي كنم سرشار از انرژي هستم.",
            "33- به  ندرت به احساسات و عواطفي كه محيط هاي متفاوت به وجود  مي آورند توجه مي كنم .",
            "34- اغلب آشنايانم مرا دوست دارند.",
            "35- براي رسيدن به اهدافم شديداً تلاش مي كنم.",
            "36- اغلب از طرز برخورد ديگران با خودم عصباني مي شوم.",
            "37- فردي خوشحال و بشاش و داراي روحيه خوبي هستم.",
            "38- معتقدم كه هنگام تصميم گيري درباره مسائل اخلاقي بايد از مراجع مذهبي پيروي كنيم.",
            "39- برخي فكر مي كنند كه من فردي سرد و حسابگر هستم.",
            "40- وقتي قول يا تعهدي مي دهم، همواره مي توان براي عمل به آن روي من حساب كرد.",
            "41-  غالبا وقتي كارها پيش نمي روند، دلسرد شده و از كار صرف نظر مي كنم.",
            "42- شخص با نشاط و خوش بيني نيستم.",
            "43- بعضي اوقات وقتي شعري را مي خوانم يا يك كار هنري را تماشا مي كنم، يك احساس لرزش و يك تكان هيجاني را حس مي كنم.",
            "44- در روش هايم سرسخت و بي انعطاف هستم.",
            "45- گاهي آن طور كه بايد و شايد قابل اعتماد و اتكاء نيستم.",
            "46- به ندرت غمگين و افسرده مي شوم .",
            "47- زندگي و رويدادهاي آن برايم  سريع مي گذرند.",
            "48- علاقه اي به تامل و تفكر جدي درباره سرنوشت و ماهيت جهان يا انسان ندارم.",
            "49- عموماً سعي مي كنم شخصي با ملاحظه و منطقي باشم.",
            "50- فرد مولدي هستم كه هميشه كارهايم را به اتمام مي رسانم.",
            "51- اغلب احساس درماندگي مي كنم و دنبال كسي مي گردم كه مشكلاتم را برطرف كند.",
            "52- شخص بسيار فعالي هستم.",
            "53- من كنجكاوي فكري فراواني دارم.",
            "54- اگر كسي را دوست نداشته باشم،مي گذارم متوجه اين احساسم بشود.",
            "55- فكر نمي كنم كه هيچ وقت بتوانم فردي منطقي بشوم.",
            "56- گاهي آنچنان خجالت زده شده ام كه فقط مي خواستم خود را پنهان كنم.",
            "57- ترجيح مي دهم كه براي خودم كار كنم تا راهبر ديگران باشم.",
            "58- اغلب از كلنجار رفتن با نظريه ها يا مفاهيم انتزاعي لذت مي برم.",
            "59- اگر لازم باشد مي توانم براي رسيدن به اهدافم ديگران را به طور ماهرانه اي به كار بگيرم.",
            "60- تلاش مي كنم هر كاري را به نحو ماهرانه اي انجام دهم."
        ]
        
        # Import personality questions
        for i, question in enumerate(personality_questions):
            cursor.execute(
                """INSERT INTO exam_questions 
                   (question_text, question_type, question_order) 
                   VALUES (?, ?, ?)""",
                (question, 'personality', i+1)
            )
        
        # Import puzzle questions (next 15 questions)
        puzzle_questions = [
            {
                "question_text": "کدام مسیر انسان را به خانه می‌رساند؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "path_finding",
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
                    ],
                    "correct_answer": "3"
                }
            },
            {
                "question_text": "کدام قطعه جای خالی را پر می‌کند؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "pattern_match",
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
                    ],
                    "correct_answer": "0"
                }
            },
            {
                "question_text": "کدام رنگ الگوی داده شده را تکمیل می‌کند؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "color_pattern",
                    "pattern": ["red", "blue", "green", "red", "blue", "?"],
                    "options": [
                        {"value": "green", "text": "سبز"},
                        {"value": "yellow", "text": "زرد"},
                        {"value": "blue", "text": "آبی"},
                        {"value": "red", "text": "قرمز"}
                    ],
                    "correct_answer": "0"
                }
            },
            {
                "question_text": "کدام تصویر خانه را نمایش می‌دهد؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "image_recognition",
                    "images": [
                        "building.svg",
                        "house.svg",
                        "tower.svg",
                        "cabin.svg"
                    ],
                    "options": [
                        {"value": "building", "text": "ساختمان"},
                        {"value": "house", "text": "خانه"},
                        {"value": "tower", "text": "برج"},
                        {"value": "cabin", "text": "کلبه"}
                    ],
                    "correct_answer": "1"
                }
            },
            {
                "question_text": "کدام عدد در دنباله زیر باید قرار بگیرد؟ 2, 4, 8, 16, ?",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "number_sequence",
                    "sequence": [2, 4, 8, 16],
                    "options": [
                        {"value": 24, "text": "24"},
                        {"value": 32, "text": "32"},
                        {"value": 30, "text": "30"},
                        {"value": 18, "text": "18"}
                    ],
                    "correct_answer": "1"
                }
            },
            {
                "question_text": "با کدام حرکت میتوانید مهره سیاه را به گوشه برسانید؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "chess_move",
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
                    ],
                    "correct_answer": "2"
                }
            },
            {
                "question_text": "کدام گزینه دنباله حروف را کامل می‌کند؟ A, C, E, G, ?",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "letter_sequence",
                    "sequence": ["A", "C", "E", "G"],
                    "options": [
                        {"value": "I", "text": "I"},
                        {"value": "J", "text": "J"},
                        {"value": "H", "text": "H"},
                        {"value": "K", "text": "K"}
                    ],
                    "correct_answer": "0"
                }
            },
            {
                "question_text": "کدام شکل با الگوی داده شده مطابقت دارد؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "shape_pattern",
                    "pattern": ["circle", "square", "triangle", "circle", "square", "?"],
                    "options": [
                        {"value": "triangle", "text": "مثلث"},
                        {"value": "square", "text": "مربع"},
                        {"value": "circle", "text": "دایره"},
                        {"value": "pentagon", "text": "پنج ضلعی"}
                    ],
                    "correct_answer": "0"
                }
            },
            {
                "question_text": "کدام تصویر با بقیه متفاوت است؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "odd_one_out",
                    "options": [
                        {"value": "apple", "text": "سیب"},
                        {"value": "orange", "text": "پرتقال"},
                        {"value": "banana", "text": "موز"},
                        {"value": "carrot", "text": "هویج"}
                    ],
                    "correct_answer": "3"
                }
            },
            {
                "question_text": "کدام قطعه پازل تصویر را کامل می‌کند؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "jigsaw",
                    "missing_piece": [2, 2],
                    "options": [
                        {"value": "piece1", "text": "قطعه 1"},
                        {"value": "piece2", "text": "قطعه 2"},
                        {"value": "piece3", "text": "قطعه 3"},
                        {"value": "piece4", "text": "قطعه 4"}
                    ],
                    "correct_answer": "2"
                }
            },
            {
                "question_text": "با توجه به الگوی اعداد، عدد بعدی کدام است؟ 3, 6, 12, 24, ?",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "number_sequence",
                    "sequence": [3, 6, 12, 24],
                    "options": [
                        {"value": 36, "text": "36"},
                        {"value": 48, "text": "48"},
                        {"value": 30, "text": "30"},
                        {"value": 42, "text": "42"}
                    ],
                    "correct_answer": "1"
                }
            },
            {
                "question_text": "کدام تصویر منطقی الگوی داده شده را ادامه می‌دهد؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "logical_sequence",
                    "options": [
                        {"value": "option1", "text": "گزینه 1"},
                        {"value": "option2", "text": "گزینه 2"},
                        {"value": "option3", "text": "گزینه 3"},
                        {"value": "option4", "text": "گزینه 4"}
                    ],
                    "correct_answer": "2"
                }
            },
            {
                "question_text": "کدام عبارت با بقیه متفاوت است؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "verbal_odd_one_out",
                    "options": [
                        {"value": "dog", "text": "سگ"},
                        {"value": "cat", "text": "گربه"},
                        {"value": "elephant", "text": "فیل"},
                        {"value": "table", "text": "میز"}
                    ],
                    "correct_answer": "3"
                }
            },
            {
                "question_text": "کدام کلید را باید فشار دهید تا قفل باز شود؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "lock_puzzle",
                    "lock_pattern": "3, 5, 7, ?",
                    "options": [
                        {"value": 9, "text": "9"},
                        {"value": 11, "text": "11"},
                        {"value": 8, "text": "8"},
                        {"value": 10, "text": "10"}
                    ],
                    "correct_answer": "1"
                }
            },
            {
                "question_text": "کدام مسیر شما را از هزارتو خارج می‌کند؟",
                "question_type": "puzzle",
                "question_data": {
                    "puzzle_type": "maze",
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
                        {"value": "path1", "text": "راه راست، پایین، راست، پایین، راست، پایین"},
                        {"value": "path2", "text": "راه پایین، راست، پایین، پایین، راست، پایین"},
                        {"value": "path3", "text": "راه پایین، پایین، راست، پایین، راست، پایین"},
                        {"value": "path4", "text": "راه راست، پایین، راست، پایین، راست، راست، پایین"}
                    ],
                    "correct_answer": "0"
                }
            }
        ]
        
        # Import puzzle questions (starting from question 61)
        for i, question in enumerate(puzzle_questions):
            cursor.execute(
                """INSERT INTO exam_questions 
                   (question_text, question_type, question_data, question_order) 
                   VALUES (?, ?, ?, ?)""",
                (
                    question["question_text"], 
                    "puzzle", 
                    json.dumps(question["question_data"]), 
                    61 + i
                )
            )
        
        print(f"Imported {len(personality_questions)} personality questions and {len(puzzle_questions)} puzzle questions.")
    
    conn.commit()
    conn.close()


def get_all_questions() -> List[Dict[str, Any]]:
    """Get all personality questions from the database - for backwards compatibility"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM personality_questions")
    questions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return questions


def get_question_by_id(question_id: int) -> Optional[Dict[str, Any]]:
    """Get a question by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM exam_questions WHERE id = ?", (question_id,))
    question = cursor.fetchone()
    
    conn.close()
    
    if question:
        result = dict(question)
        # Parse question_data for puzzle questions
        if result["question_type"] == "puzzle" and result["question_data"]:
            result["question_data"] = json.loads(result["question_data"])
        return result
    
    return None


def get_question_by_order(order: int) -> Optional[Dict[str, Any]]:
    """Get a question by its order number"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM exam_questions WHERE question_order = ?", (order,))
    question = cursor.fetchone()
    
    conn.close()
    
    if question:
        result = dict(question)
        # Parse question_data for puzzle questions
        if result["question_type"] == "puzzle" and result["question_data"]:
            result["question_data"] = json.loads(result["question_data"])
        return result
    
    return None


def get_total_questions() -> int:
    """Get the total number of exam questions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM exam_questions")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    return count


def save_exam_response(user_id: int, question_id: int, response: str, attempts: int = 1, score: Optional[float] = None) -> int:
    """Save a user's response to a question"""
    from datetime import datetime
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    
    cursor.execute('''
    INSERT INTO exam_responses (user_id, question_id, response, attempts, score, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, question_id, response, attempts, score, created_at))
    
    response_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return response_id


def get_user_progress(user_id: int) -> int:
    """Get the number of questions a user has completed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT COUNT(DISTINCT question_id) FROM exam_responses
    WHERE user_id = ?
    """, (user_id,))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count


def has_user_answered_question(user_id: int, question_id: int) -> bool:
    """Check if a user has already answered a specific question"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id FROM exam_responses
    WHERE user_id = ? AND question_id = ?
    """, (user_id, question_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None


def mark_exam_completed(user_id: int) -> None:
    """Mark that a user has completed the exam"""
    from datetime import datetime
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    completion_date = datetime.now().isoformat()
    
    # Check if user already has an entry in completed_exams
    cursor.execute("SELECT id FROM completed_exams WHERE user_id = ?", (user_id,))
    existing_entry = cursor.fetchone()
    
    if not existing_entry:
        cursor.execute('''
        INSERT INTO completed_exams (user_id, completion_date)
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


def calculate_score(user_id: int) -> Dict[str, Any]:
    """
    Calculate the exam scores for a user (both personality and puzzle sections)
    
    Args:
        user_id (int): The user ID
        
    Returns:
        Dict[str, Any]: The calculated scores
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all responses for the user with question details
    cursor.execute("""
        SELECT q.id, q.question_text, q.question_type, r.response, r.attempts, r.score
        FROM exam_responses r
        JOIN exam_questions q ON r.question_id = q.id
        WHERE r.user_id = ?
        ORDER BY q.question_order
    """, (user_id,))
    
    responses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Separate responses by type
    personality_responses = [r for r in responses if r['question_type'] == 'personality']
    puzzle_responses = [r for r in responses if r['question_type'] == 'puzzle']
    
    # Calculate personality scores - this is a placeholder for your actual scoring logic
    personality_scores = {
        "openness": 0,
        "conscientiousness": 0,
        "extraversion": 0,
        "agreeableness": 0,
        "neuroticism": 0
    }
    
    # Simple example of personality scoring
    for response in personality_responses:
        question_id = response["id"]
        answer_value = int(response["response"])
        
        # Map questions to traits (this would be based on your test design)
        # Example mapping logic - replace with your actual mapping
        if question_id % 5 == 0:
            personality_scores["openness"] += answer_value
        elif question_id % 5 == 1:
            personality_scores["conscientiousness"] += answer_value
        elif question_id % 5 == 2:
            personality_scores["extraversion"] += answer_value
        elif question_id % 5 == 3:
            personality_scores["agreeableness"] += answer_value
        elif question_id % 5 == 4:
            personality_scores["neuroticism"] += answer_value
    
    # Normalize personality scores
    personality_total_questions = len(personality_responses)
    if personality_total_questions > 0:
        for trait in personality_scores:
            max_possible = personality_total_questions / 5 * 5  # Assuming 5 is max value per question
            personality_scores[trait] = round((personality_scores[trait] / max_possible) * 100, 2)
    
    # Calculate puzzle scores
    puzzle_total = len(puzzle_responses)
    puzzle_perfect = sum(1 for r in puzzle_responses if r['score'] == 1.0)
    puzzle_partial = sum(1 for r in puzzle_responses if r['score'] == 0.5)
    puzzle_failed = sum(1 for r in puzzle_responses if r['score'] == 0.0)
    
    total_points = sum(float(r['score'] or 0) for r in puzzle_responses)
    average_score = total_points / puzzle_total if puzzle_total > 0 else 0
    
    puzzle_scores = {
        "total_score": total_points,
        "average_score": round(average_score, 2),
        "total_puzzles": puzzle_total,
        "perfect_score_puzzles": puzzle_perfect,
        "partial_score_puzzles": puzzle_partial,
        "failed_puzzles": puzzle_failed
    }
    
    # Combined result
    return {
        "personality": personality_scores,
        "puzzle": puzzle_scores,
        "completed_questions": len(responses),
        "total_questions": get_total_questions()
    }


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
        
        # Delete old responses as well (for backwards compatibility)
        cursor.execute("DELETE FROM exam_responses_old WHERE user_id = ?", (user_id,))
        
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


def get_user_report_data(user_id: int):
    """
    Get user details and exam responses for reporting
    """
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
    
    # Get exam responses with question text
    cursor.execute("""
        SELECT r.id, q.question_text, q.question_type, r.response, r.attempts, r.score, r.created_at,
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
                    if isinstance(options[option_index], dict):
                        response["response_text"] = options[option_index].get("text", options[option_index].get("value", ""))
                    else:
                        response["response_text"] = options[option_index]
                except (ValueError, IndexError):
                    response["response_text"] = response["response"]
                
                # Add score information
                if response["score"] == 1.0:
                    response["score_text"] = "امتیاز کامل (1.0)"
                elif response["score"] == 0.5:
                    response["score_text"] = "امتیاز نسبی (0.5)"
                else:
                    response["score_text"] = "امتیاز صفر (0.0)"
            else:
                response["response_text"] = response["response"]
    
    conn.close()
    
    return user_details, responses