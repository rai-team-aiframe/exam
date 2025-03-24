# app/admin_db.py
import sqlite3
import bcrypt
import os
from datetime import datetime
from typing import Optional, Dict, Any

def get_admin_db_connection():
    """Create a connection to the admin SQLite database"""
    conn = sqlite3.connect('admin.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_admin_db():
    """Initialize the admin database with required tables and default admin account"""
    # Also ensure the admins table exists in the main database
    ensure_admins_table_in_main_db()
    
    conn = get_admin_db_connection()
    cursor = conn.cursor()
    
    # Create admins table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Check if default admin exists
    cursor.execute("SELECT COUNT(*) FROM admins WHERE username = ?", ("anonymous_1",))
    admin_exists = cursor.fetchone()[0] > 0
    
    # Create default admin if not exists
    if not admin_exists:
        # Hash the password
        password = "Anonymous.4050*"
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # Insert default admin
        cursor.execute(
            "INSERT INTO admins (username, password, created_at) VALUES (?, ?, ?)",
            ("anonymous_1", hashed_password, datetime.now().isoformat())
        )
    
    conn.commit()
    conn.close()

def ensure_admins_table_in_main_db():
    """Ensure admins table exists in the main database too for proper joining"""
    try:
        # Connect to the main database
        conn = sqlite3.connect('online_exam.db')
        cursor = conn.cursor()
        
        # Create admins table in the main database if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        ''')
        
        # Check if the default admin exists in the main database
        cursor.execute("SELECT COUNT(*) FROM admins WHERE username = ?", ("anonymous_1",))
        admin_exists = cursor.fetchone()[0] > 0
        
        # Create default admin if not exists
        if not admin_exists:
            # Hash the password
            password = "Anonymous.4050*"
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            # Insert default admin
            cursor.execute(
                "INSERT INTO admins (username, password, created_at) VALUES (?, ?, ?)",
                ("anonymous_1", hashed_password, datetime.now().isoformat())
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error ensuring admins table in main DB: {e}")

def get_admin_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get admin by username"""
    conn = get_admin_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
    admin = cursor.fetchone()
    
    conn.close()
    
    if admin:
        return dict(admin)
    return None

def verify_admin_password(plain_password: str, hashed_password: str) -> bool:
    """Verify an admin password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))