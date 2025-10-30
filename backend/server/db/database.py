"""WOO Backend Database and helper functions"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any


DB_PATH = Path(__file__).with_name("database.sqlite3")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection() -> sqlite3.Connection:
    """Return a sqlite3 connection with sane defaults for this app."""
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    # Enforce foreign keys per connection (SQLite requires it per session)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create the database file and apply schema if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            connection.executescript(schema_file.read())


# ---------------------
# Helper query functions
# ---------------------

def get_users() -> List[Dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT uuid, email, name, role FROM Users ORDER BY uuid ASC"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT uuid, email, name, role FROM Users WHERE email = ?",
            (email,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_user(
    *,
    email: str,
    password: str,
    name: Optional[str] = None,
    role: Optional[str] = None,
    picture: Optional[bytes] = None,
) -> int:
    """Insert a user and return its generated uuid.

    Note: password storage here is plain for simplicity; replace with a proper
    hashing scheme (e.g., bcrypt/argon2) in production.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO Users (email, password, name, picture, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, password, name, picture, role),
        )
        return int(cursor.lastrowid)


# ---------------------
# WOO Case functions
# ---------------------

def get_woo_cases() -> List[Dict[str, Any]]:
    """Get all WOO cases."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT uuid, title, description, requester, document_IDs FROM WOO_Case ORDER BY uuid ASC"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_woo_case_by_id(case_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific WOO case by ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT uuid, title, description, requester, document_IDs FROM WOO_Case WHERE uuid = ?",
            (case_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


# ---------------------
# Document functions
# ---------------------

def get_documents() -> List[Dict[str, Any]]:
    """Get all documents."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT uuid, title, description, type FROM Document ORDER BY uuid ASC"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific document by ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT uuid, title, description, type FROM Document WHERE uuid = ?",
            (doc_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


# ---------------------
# Stakeholder functions
# ---------------------

def get_stakeholders() -> List[Dict[str, Any]]:
    """Get all stakeholders."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT uuid, type, name, contact_info FROM Stakeholders ORDER BY uuid ASC"
        )
        return [dict(row) for row in cursor.fetchall()]


