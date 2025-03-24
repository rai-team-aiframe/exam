# app/superuser_db.py
import sqlite3
import bcrypt
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

def get_superuser_db_connection():
    """Create a connection to the superuser SQLite database"""
    conn = sqlite3.connect('superuser.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_superuser_db():
    """Initialize the superuser database with required tables and default superuser account"""
    conn = get_superuser_db_connection()
    cursor = conn.cursor()
    
    # Create superusers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS superusers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Check if default superuser exists
    cursor.execute("SELECT COUNT(*) FROM superusers WHERE username = ?", ("Moein",))
    superuser_exists = cursor.fetchone()[0] > 0
    
    # Create default superuser if not exists
    if not superuser_exists:
        # Hash the password
        password = "Moein.9080*"
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # Insert default superuser
        cursor.execute(
            "INSERT INTO superusers (username, password, created_at) VALUES (?, ?, ?)",
            ("Moein", hashed_password, datetime.now().isoformat())
        )
        
        print("Default superuser created with username: Moein and password: Moein.9080*")
    
    conn.commit()
    conn.close()

def get_superuser_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get superuser by username"""
    conn = get_superuser_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM superusers WHERE username = ?", (username,))
    superuser = cursor.fetchone()
    
    conn.close()
    
    if superuser:
        return dict(superuser)
    return None

def verify_superuser_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a superuser password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_all_admins() -> List[Dict[str, Any]]:
    """Get all admin accounts"""
    from app.admin_db import get_admin_db_connection
    
    conn = get_admin_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM admins ORDER BY created_at DESC
    ''')
    
    admins = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return admins

def create_admin(
    username: str, 
    password: str, 
    full_name: str = "", 
    job_field: str = "", 
    id_number: str = "", 
    phone_number: str = ""
) -> int:
    """Create a new admin account"""
    from app.admin_db import get_admin_db_connection
    
    conn = get_admin_db_connection()
    cursor = conn.cursor()
    
    # Check if admin with this username already exists
    cursor.execute("SELECT id FROM admins WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"نام کاربری '{username}' قبلاً استفاده شده است.")
        
    # Hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    created_at = datetime.now().isoformat()
    
    # Create admin account (simple version)
    cursor.execute('''
    INSERT INTO admins (username, password, created_at) 
    VALUES (?, ?, ?)
    ''', (username, hashed_password, created_at))
    
    # Get the ID of the newly created admin
    admin_id = cursor.lastrowid
    
    # Create extended admin profile if fields provided
    if any([full_name, job_field, id_number, phone_number]):
        # Check if admin_profiles table exists, if not create it
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_profiles (
            admin_id INTEGER PRIMARY KEY,
            full_name TEXT,
            job_field TEXT,
            id_number TEXT,
            phone_number TEXT,
            FOREIGN KEY (admin_id) REFERENCES admins (id)
        )
        ''')
        
        # Insert admin profile
        cursor.execute('''
        INSERT INTO admin_profiles (admin_id, full_name, job_field, id_number, phone_number)
        VALUES (?, ?, ?, ?, ?)
        ''', (admin_id, full_name, job_field, id_number, phone_number))
    
    conn.commit()
    conn.close()
    
    return admin_id

def update_admin(
    admin_id: int,
    username: str = None,
    password: str = None,
    full_name: str = None,
    job_field: str = None,
    id_number: str = None,
    phone_number: str = None
) -> bool:
    """Update an admin account"""
    from app.admin_db import get_admin_db_connection
    
    conn = get_admin_db_connection()
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT id FROM admins WHERE id = ?", (admin_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("مدیر مورد نظر یافت نشد.")
    
    # Update admin basic info
    if username or password:
        # Build update query dynamically
        update_fields = []
        params = []
        
        if username:
            # Check if username already exists for another admin
            cursor.execute("SELECT id FROM admins WHERE username = ? AND id != ?", (username, admin_id))
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"نام کاربری '{username}' قبلاً استفاده شده است.")
            update_fields.append("username = ?")
            params.append(username)
        
        if password:
            # Hash the new password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            update_fields.append("password = ?")
            params.append(hashed_password)
        
        if update_fields:
            query = f"UPDATE admins SET {', '.join(update_fields)} WHERE id = ?"
            params.append(admin_id)
            cursor.execute(query, params)
    
    # Check if admin_profiles table exists
    cursor.execute('''
    SELECT name FROM sqlite_master WHERE type='table' AND name='admin_profiles'
    ''')
    profiles_table_exists = cursor.fetchone() is not None
    
    if not profiles_table_exists:
        # Create the table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_profiles (
            admin_id INTEGER PRIMARY KEY,
            full_name TEXT,
            job_field TEXT,
            id_number TEXT,
            phone_number TEXT,
            FOREIGN KEY (admin_id) REFERENCES admins (id)
        )
        ''')
    
    # Check if profile already exists
    cursor.execute("SELECT admin_id FROM admin_profiles WHERE admin_id = ?", (admin_id,))
    profile_exists = cursor.fetchone() is not None
    
    if profile_exists:
        # Update existing profile
        if any([full_name is not None, job_field is not None, id_number is not None, phone_number is not None]):
            update_fields = []
            params = []
            
            if full_name is not None:
                update_fields.append("full_name = ?")
                params.append(full_name)
            
            if job_field is not None:
                update_fields.append("job_field = ?")
                params.append(job_field)
            
            if id_number is not None:
                update_fields.append("id_number = ?")
                params.append(id_number)
            
            if phone_number is not None:
                update_fields.append("phone_number = ?")
                params.append(phone_number)
            
            if update_fields:
                query = f"UPDATE admin_profiles SET {', '.join(update_fields)} WHERE admin_id = ?"
                params.append(admin_id)
                cursor.execute(query, params)
    else:
        # Create new profile
        cursor.execute('''
        INSERT INTO admin_profiles (admin_id, full_name, job_field, id_number, phone_number)
        VALUES (?, ?, ?, ?, ?)
        ''', (admin_id, full_name or "", job_field or "", id_number or "", phone_number or ""))
    
    conn.commit()
    conn.close()
    
    return True

def delete_admin(admin_id: int) -> bool:
    """Delete an admin account"""
    from app.admin_db import get_admin_db_connection
    
    conn = get_admin_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if admin exists
        cursor.execute("SELECT id FROM admins WHERE id = ?", (admin_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError("مدیر مورد نظر یافت نشد.")
        
        # Delete admin profile if it exists
        cursor.execute("DELETE FROM admin_profiles WHERE admin_id = ?", (admin_id,))
        
        # Delete admin
        cursor.execute("DELETE FROM admins WHERE id = ?", (admin_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e

def get_admin_with_profile(admin_id: int) -> Optional[Dict[str, Any]]:
    """Get admin account with profile data"""
    from app.admin_db import get_admin_db_connection
    
    conn = get_admin_db_connection()
    cursor = conn.cursor()
    
    # Check if admin_profiles table exists
    cursor.execute('''
    SELECT name FROM sqlite_master WHERE type='table' AND name='admin_profiles'
    ''')
    profiles_table_exists = cursor.fetchone() is not None
    
    if profiles_table_exists:
        # Get admin with profile data
        cursor.execute('''
        SELECT a.id, a.username, a.created_at, 
               p.full_name, p.job_field, p.id_number, p.phone_number
        FROM admins a
        LEFT JOIN admin_profiles p ON a.id = p.admin_id
        WHERE a.id = ?
        ''', (admin_id,))
    else:
        # Get admin data only
        cursor.execute('''
        SELECT id, username, created_at, 
               "" as full_name, "" as job_field, "" as id_number, "" as phone_number
        FROM admins
        WHERE id = ?
        ''', (admin_id,))
    
    admin = cursor.fetchone()
    conn.close()
    
    if admin:
        return dict(admin)
    return None

def get_all_admins_with_profiles() -> List[Dict[str, Any]]:
    """Get all admin accounts with their profile data"""
    from app.admin_db import get_admin_db_connection
    
    conn = get_admin_db_connection()
    cursor = conn.cursor()
    
    # Check if admin_profiles table exists
    cursor.execute('''
    SELECT name FROM sqlite_master WHERE type='table' AND name='admin_profiles'
    ''')
    profiles_table_exists = cursor.fetchone() is not None
    
    if profiles_table_exists:
        # Get admins with profile data
        cursor.execute('''
        SELECT a.id, a.username, a.created_at, 
               p.full_name, p.job_field, p.id_number, p.phone_number
        FROM admins a
        LEFT JOIN admin_profiles p ON a.id = p.admin_id
        ORDER BY a.created_at DESC
        ''')
    else:
        # Get admin data only
        cursor.execute('''
        SELECT id, username, created_at, 
               "" as full_name, "" as job_field, "" as id_number, "" as phone_number
        FROM admins
        ORDER BY created_at DESC
        ''')
    
    admins = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return admins

def get_superuser_by_id(superuser_id: int) -> Optional[Dict[str, Any]]:
    """Get superuser by ID"""
    conn = get_superuser_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM superusers WHERE id = ?", (superuser_id,))
    superuser = cursor.fetchone()
    
    conn.close()
    
    if superuser:
        return dict(superuser)
    return None

def update_superuser_credentials(superuser_id: int, username: str = None, password: str = None) -> bool:
    """Update a superuser's credentials"""
    conn = get_superuser_db_connection()
    cursor = conn.cursor()
    
    # Check if superuser exists
    cursor.execute("SELECT id FROM superusers WHERE id = ?", (superuser_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("سوپر ادمین مورد نظر یافت نشد.")
    
    # Update superuser info
    if username or password:
        # Build update query dynamically
        update_fields = []
        params = []
        
        if username:
            # Check if username already exists for another superuser
            cursor.execute("SELECT id FROM superusers WHERE username = ? AND id != ?", (username, superuser_id))
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"نام کاربری '{username}' قبلاً استفاده شده است.")
            update_fields.append("username = ?")
            params.append(username)
        
        if password:
            # Hash the new password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            update_fields.append("password = ?")
            params.append(hashed_password)
        
        if update_fields:
            query = f"UPDATE superusers SET {', '.join(update_fields)} WHERE id = ?"
            params.append(superuser_id)
            cursor.execute(query, params)
    
    conn.commit()
    conn.close()
    
    return True