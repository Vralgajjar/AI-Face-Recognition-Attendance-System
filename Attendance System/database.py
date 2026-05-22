import sqlite3
import os

DB_PATH = "attendance.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            college TEXT NOT NULL,
            face_id INTEGER UNIQUE,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Attendance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            college TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()


def get_all_students():
    conn = get_connection()
    students = conn.execute("SELECT * FROM students ORDER BY registered_at DESC").fetchall()
    conn.close()
    return students


def get_student_by_face_id(face_id):
    conn = get_connection()
    student = conn.execute("SELECT * FROM students WHERE face_id = ?", (face_id,)).fetchone()
    conn.close()
    return student


def add_student(name, roll_number, college, face_id):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO students (name, roll_number, college, face_id) VALUES (?, ?, ?, ?)",
            (name, roll_number, college, face_id)
        )
        conn.commit()
        return True, "Student added successfully"
    except sqlite3.IntegrityError as e:
        if "roll_number" in str(e):
            return False, "Roll number already exists"
        return False, "Student already exists"
    finally:
        conn.close()


def delete_student(student_id):
    conn = get_connection()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()


def mark_attendance(student_id, name, roll_number, college, date, time):
    conn = get_connection()
    # Check duplicate
    existing = conn.execute(
        "SELECT id FROM attendance WHERE student_id = ? AND date = ?",
        (student_id, date)
    ).fetchone()
    if existing:
        conn.close()
        return False, "Attendance already marked for today"
    conn.execute(
        "INSERT INTO attendance (student_id, name, roll_number, college, date, time) VALUES (?, ?, ?, ?, ?, ?)",
        (student_id, name, roll_number, college, date, time)
    )
    conn.commit()
    conn.close()
    return True, "Attendance marked"


def get_all_attendance(date_filter=None, search=None):
    conn = get_connection()
    query = "SELECT * FROM attendance"
    params = []
    conditions = []
    if date_filter:
        conditions.append("date = ?")
        params.append(date_filter)
    if search:
        conditions.append("(name LIKE ? OR roll_number LIKE ? OR college LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY marked_at DESC"
    records = conn.execute(query, params).fetchall()
    conn.close()
    return records


def get_dashboard_stats():
    conn = get_connection()
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_attendance = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    today_attendance = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE date = date('now')"
    ).fetchone()[0]

    # Daily attendance count for chart (last 7 days)
    daily_counts = conn.execute("""
        SELECT date, COUNT(*) as count
        FROM attendance
        WHERE date >= date('now', '-6 days')
        GROUP BY date
        ORDER BY date ASC
    """).fetchall()

    conn.close()
    return {
        "total_students": total_students,
        "total_attendance": total_attendance,
        "today_attendance": today_attendance,
        "daily_counts": [dict(row) for row in daily_counts]
    }


def get_next_face_id():
    conn = get_connection()
    result = conn.execute("SELECT MAX(face_id) FROM students").fetchone()[0]
    conn.close()
    return (result or 0) + 1
