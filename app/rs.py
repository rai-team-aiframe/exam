# Run this in a Python shell or script
import sqlite3

conn = sqlite3.connect('online_exam.db')
cursor = conn.cursor()

# Add missing columns
try:
    cursor.execute("ALTER TABLE exam_responses ADD COLUMN attempts INTEGER DEFAULT 1")
    print("Added 'attempts' column to exam_responses table")
except sqlite3.OperationalError as e:
    print(f"Note: {e}")

try:
    cursor.execute("ALTER TABLE exam_responses ADD COLUMN score REAL DEFAULT NULL")
    print("Added 'score' column to exam_responses table")
except sqlite3.OperationalError as e:
    print(f"Note: {e}")

conn.commit()
conn.close()
print("Database update complete")