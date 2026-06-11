"""
database/db_manager.py
=======================
SQLite database layer for EmotionSense AI.

Tables
------
users           — login credentials (hashed passwords)
emotion_logs    — every emotion analysis result
"""

import sqlite3
import hashlib
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), "emotionsense.db")


class DatabaseManager:
    """Manages all SQLite operations for EmotionSense AI."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Connection helper
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row          # dict-like rows
        return conn

    # ------------------------------------------------------------------
    # Schema creation
    # ------------------------------------------------------------------
    def initialize(self):
        """Create tables if they don't exist (idempotent)."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    username    TEXT    UNIQUE NOT NULL,
                    password    TEXT    NOT NULL,
                    created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS emotion_logs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER NOT NULL,
                    input_text      TEXT,
                    source          TEXT DEFAULT 'text',   -- 'text' or 'voice'
                    primary_emotion TEXT,
                    confidence      REAL,
                    stress_level    REAL,
                    all_scores      TEXT,                  -- JSON string
                    timestamp       TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            """)

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------
    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, password: str) -> tuple[bool, str]:
        """Register a new user. Returns (success, message)."""
        if not username.strip() or not password.strip():
            return False, "Username and password cannot be empty."
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username.strip(), self._hash(password))
                )
            return True, "Account created successfully!"
        except sqlite3.IntegrityError:
            return False, "Username already exists. Please choose another."

    def authenticate_user(self, username: str, password: str) -> tuple[bool, dict | None]:
        """Verify credentials. Returns (success, user_row)."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username.strip(), self._hash(password))
            ).fetchone()
        if row:
            return True, dict(row)
        return False, None

    # ------------------------------------------------------------------
    # Emotion log operations
    # ------------------------------------------------------------------
    def log_emotion(self, user_id: int, input_text: str, source: str,
                    primary_emotion: str, confidence: float,
                    stress_level: float, all_scores: str):
        """Insert a single emotion analysis record."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO emotion_logs
                    (user_id, input_text, source, primary_emotion,
                     confidence, stress_level, all_scores, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, input_text, source, primary_emotion,
                round(confidence, 2), round(stress_level, 2),
                all_scores, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

    def get_history(self, user_id: int, limit: int = 100) -> list[dict]:
        """Fetch emotion history for a user (newest first)."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM emotion_logs
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self, user_id: int) -> dict:
        """Aggregate emotion statistics for the dashboard."""
        with self._get_conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS n FROM emotion_logs WHERE user_id = ?",
                (user_id,)
            ).fetchone()["n"]

            freq = conn.execute("""
                SELECT primary_emotion, COUNT(*) AS cnt
                FROM emotion_logs WHERE user_id = ?
                GROUP BY primary_emotion
                ORDER BY cnt DESC
            """, (user_id,)).fetchall()

            avg_stress = conn.execute("""
                SELECT AVG(stress_level) AS avg_s
                FROM emotion_logs WHERE user_id = ?
            """, (user_id,)).fetchone()["avg_s"]

            weekly = conn.execute("""
                SELECT DATE(timestamp) AS day,
                       primary_emotion, COUNT(*) AS cnt
                FROM emotion_logs
                WHERE user_id = ?
                  AND timestamp >= DATE('now', '-7 days')
                GROUP BY day, primary_emotion
                ORDER BY day
            """, (user_id,)).fetchall()

        return {
            "total": total,
            "frequency": [dict(r) for r in freq],
            "avg_stress": round(avg_stress or 0.0, 1),
            "weekly": [dict(r) for r in weekly],
        }

    def delete_history(self, user_id: int):
        """Clear all logs for the given user."""
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM emotion_logs WHERE user_id = ?", (user_id,)
            )
