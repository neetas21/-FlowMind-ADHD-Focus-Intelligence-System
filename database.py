import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = "adhd_focus.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            priority INTEGER DEFAULT 2,  -- 1=High, 2=Medium, 3=Low
            estimated_minutes INTEGER DEFAULT 30,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            due_date TEXT,
            status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, abandoned
            delay_count INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            mood INTEGER DEFAULT 3,           -- 1-5 scale
            energy INTEGER DEFAULT 3,         -- 1-5 scale
            start_time TEXT DEFAULT (datetime('now','localtime')),
            end_time TEXT,
            planned_minutes INTEGER DEFAULT 25,
            actual_minutes REAL DEFAULT 0,
            completed INTEGER DEFAULT 0,      -- 0 or 1
            notes TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS nudges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            task_id INTEGER,
            trigger_reason TEXT,
            nudge_text TEXT,
            timestamp TEXT DEFAULT (datetime('now','localtime')),
            was_helpful INTEGER DEFAULT -1,   -- -1=not rated, 0=no, 1=yes
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()

# ── TASK CRUD ─────────────────────────────────────────────────────────────────

def add_task(title, category, priority, estimated_minutes, due_date=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tasks (title, category, priority, estimated_minutes, due_date)
        VALUES (?, ?, ?, ?, ?)
    """, (title, category, priority, estimated_minutes, due_date))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks(status=None):
    conn = get_connection()
    query = "SELECT * FROM tasks"
    if status:
        query += f" WHERE status='{status}'"
    query += " ORDER BY priority ASC, created_at DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_task_status(task_id, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    if status == 'pending':
        c.execute("UPDATE tasks SET delay_count = delay_count + 1 WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# ── SESSION CRUD ──────────────────────────────────────────────────────────────

def start_session(task_id, mood, energy, planned_minutes):
    conn = get_connection()
    c = conn.cursor()
    # Mark any lingering in_progress session as abandoned
    c.execute("""
        UPDATE sessions SET end_time=datetime('now','localtime'), completed=0
        WHERE task_id=? AND end_time IS NULL
    """, (task_id,))
    c.execute("""
        INSERT INTO sessions (task_id, mood, energy, planned_minutes)
        VALUES (?, ?, ?, ?)
    """, (task_id, mood, energy, planned_minutes))
    session_id = c.lastrowid
    c.execute("UPDATE tasks SET status='in_progress' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return session_id

def end_session(session_id, task_id, completed, notes=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT start_time, planned_minutes FROM sessions WHERE id=?", (session_id,))
    row = c.fetchone()
    actual_minutes = 0
    if row and row[0]:
        start = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        actual_minutes = round((datetime.now() - start).total_seconds() / 60, 1)

    c.execute("""
        UPDATE sessions
        SET end_time=datetime('now','localtime'), completed=?, actual_minutes=?, notes=?
        WHERE id=?
    """, (int(completed), actual_minutes, notes, session_id))

    new_status = 'completed' if completed else 'abandoned'
    c.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, task_id))
    # Re-open abandoned tasks
    if not completed:
        c.execute("UPDATE tasks SET status='pending', delay_count=delay_count+1 WHERE id=?", (task_id,))

    conn.commit()
    conn.close()
    return actual_minutes

def get_sessions(limit=200):
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT s.*, t.title as task_title, t.category, t.priority
        FROM sessions s
        LEFT JOIN tasks t ON s.task_id = t.id
        ORDER BY s.start_time DESC
        LIMIT ?
    """, conn, params=(limit,))
    conn.close()
    return df

# ── NUDGE CRUD ────────────────────────────────────────────────────────────────

def save_nudge(session_id, task_id, trigger_reason, nudge_text):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO nudges (session_id, task_id, trigger_reason, nudge_text)
        VALUES (?, ?, ?, ?)
    """, (session_id, task_id, trigger_reason, nudge_text))
    nudge_id = c.lastrowid
    conn.commit()
    conn.close()
    return nudge_id

def rate_nudge(nudge_id, helpful: bool):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE nudges SET was_helpful=? WHERE id=?", (int(helpful), nudge_id))
    conn.commit()
    conn.close()

def get_nudges(limit=50):
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT n.*, t.title as task_title
        FROM nudges n
        LEFT JOIN tasks t ON n.task_id = t.id
        ORDER BY n.timestamp DESC
        LIMIT ?
    """, conn, params=(limit,))
    conn.close()
    return df

# ── ANALYTICS QUERIES ─────────────────────────────────────────────────────────

def get_daily_summary():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            date(start_time) as date,
            COUNT(*) as total_sessions,
            SUM(completed) as completed_sessions,
            SUM(actual_minutes) as total_focus_minutes,
            AVG(mood) as avg_mood,
            AVG(energy) as avg_energy,
            AVG(actual_minutes) as avg_session_minutes
        FROM sessions
        WHERE start_time IS NOT NULL
        GROUP BY date(start_time)
        ORDER BY date ASC
    """, conn)
    conn.close()
    return df

def get_hourly_productivity():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            CAST(strftime('%H', start_time) AS INTEGER) as hour,
            AVG(completed) as completion_rate,
            AVG(actual_minutes) as avg_focus,
            COUNT(*) as session_count
        FROM sessions
        WHERE start_time IS NOT NULL
        GROUP BY hour
        ORDER BY hour
    """, conn)
    conn.close()
    return df

def get_procrastination_data():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            t.id, t.title, t.category, t.priority,
            t.delay_count,
            t.estimated_minutes,
            COUNT(s.id) as total_sessions,
            SUM(s.completed) as completed_sessions,
            AVG(s.actual_minutes) as avg_actual_minutes,
            AVG(s.mood) as avg_mood,
            AVG(s.energy) as avg_energy
        FROM tasks t
        LEFT JOIN sessions s ON t.id = s.task_id
        GROUP BY t.id
    """, conn)
    conn.close()
    return df
