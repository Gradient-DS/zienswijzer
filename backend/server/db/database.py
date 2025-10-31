"""WOO Backend Database and helper functions"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


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
# User functions
# ---------------------


def get_users() -> List[Dict[str, Any]]:
    """Get all users."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT id, username, email, avatar, created_at, updated_at FROM Users ORDER BY created_at ASC"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get a user by ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT id, username, email, avatar, created_at, updated_at FROM Users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT id, username, email, avatar, created_at, updated_at FROM Users WHERE email = ?",
            (email,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get a user by username."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT id, username, email, avatar, created_at, updated_at FROM Users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


# ---------------------
# Workspace functions
# ---------------------


def get_workspaces(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all workspaces, optionally filtered by user membership."""
    with get_connection() as connection:
        if user_id:
            cursor = connection.execute(
                """
                SELECT w.id, w.name, w.description, w.created_at, w.updated_at, w.owner_id,
                       (SELECT COUNT(*) FROM WorkspaceMembers WHERE workspace_id = w.id) as member_count,
                       wm.is_owner
                FROM Workspaces w
                JOIN WorkspaceMembers wm ON w.id = wm.workspace_id
                WHERE wm.user_id = ?
                ORDER BY w.created_at DESC
            """,
                (user_id,),
            )
        else:
            cursor = connection.execute(
                """
                SELECT w.id, w.name, w.description, w.created_at, w.updated_at, w.owner_id,
                       (SELECT COUNT(*) FROM WorkspaceMembers WHERE workspace_id = w.id) as member_count
                FROM Workspaces w
                ORDER BY w.created_at DESC
            """
            )
        return [dict(row) for row in cursor.fetchall()]


def get_workspace_by_id(workspace_id: str) -> Optional[Dict[str, Any]]:
    """Get a workspace by ID with member count."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT w.id, w.name, w.description, w.created_at, w.updated_at, w.owner_id,
                   (SELECT COUNT(*) FROM WorkspaceMembers WHERE workspace_id = w.id) as member_count
            FROM Workspaces w
            WHERE w.id = ?
        """,
            (workspace_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_workspace_members(workspace_id: str) -> List[Dict[str, Any]]:
    """Get all members of a workspace."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT u.id, u.username, u.email, u.avatar, wm.is_owner, wm.joined_at
            FROM Users u
            JOIN WorkspaceMembers wm ON u.id = wm.user_id
            WHERE wm.workspace_id = ?
            ORDER BY wm.is_owner DESC, wm.joined_at ASC
        """,
            (workspace_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def create_workspace(workspace: Dict[str, Any]) -> None:
    """Create a new workspace."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO Workspaces (id, name, description, created_at, updated_at, owner_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                workspace["id"],
                workspace["name"],
                workspace["description"],
                workspace["created_at"],
                workspace["updated_at"],
                workspace["owner_id"],
            ),
        )
        # Add workspace members
        for member in workspace["members"]:
            connection.execute(
                """
                INSERT INTO WorkspaceMembers (workspace_id, user_id, is_owner, joined_at)
                VALUES (?, ?, ?, ?)
            """,
                (workspace["id"], member["id"], member["is_owner"], member["joined_at"]),
            )
        connection.commit()


# ---------------------
# Case functions
# ---------------------


def get_cases() -> List[Dict[str, Any]]:
    """Get all cases."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT id, title, description, created_at, updated_at FROM Cases ORDER BY created_at DESC"
        )
        cases = [dict(row) for row in cursor.fetchall()]

        # Add document IDs to each case
        for case in cases:
            doc_cursor = connection.execute("SELECT document_id FROM CaseDocuments WHERE case_id = ?", (case["id"],))
            case["documentIds"] = [row["document_id"] for row in doc_cursor.fetchall()]

        return cases


def get_case_by_id(case_id: str) -> Optional[Dict[str, Any]]:
    """Get a case by ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT id, title, description, created_at, updated_at FROM Cases WHERE id = ?",
            (case_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        case = dict(row)

        # Add document IDs
        doc_cursor = connection.execute("SELECT document_id FROM CaseDocuments WHERE case_id = ?", (case_id,))
        case["documentIds"] = [r["document_id"] for r in doc_cursor.fetchall()]

        return case


def create_case(case: Dict[str, Any]) -> None:
    """Create a new case."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO Cases (id, title, description, password, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (case["id"], case["title"], case["description"], case["password"], case["created_at"], case["updated_at"]),
        )
        connection.commit()


# ---------------------
# Document functions
# ---------------------


def get_documents() -> List[Dict[str, Any]]:
    """Get all documents."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, title, description, type, file_path, file_size, page_count,
                   processing_status, uploaded_at, processed_at, created_at, updated_at
            FROM Documents
            ORDER BY created_at DESC
        """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_document_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a document by ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, title, description, type, file_path, file_size, page_count,
                   processing_status, uploaded_at, processed_at, created_at, updated_at
            FROM Documents
            WHERE id = ?
        """,
            (doc_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_document(document: Dict[str, Any]) -> None:
    """Create a new document."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO Documents (id, title, description, type, file_path, file_size, page_count, processing_status, uploaded_at, processed_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                document["id"],
                document["title"],
                document["description"],
                document["type"],
                document["file_path"],
                document["file_size"],
                document["page_count"],
                document["processing_status"],
                document["uploaded_at"],
                document["processed_at"],
                document["created_at"],
                document["updated_at"],
            ),
        )
        connection.commit()


def add_document_to_case(case_id: str, document_id: str) -> None:
    """Add a document to a case."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO CaseDocuments (case_id, document_id, added_at)
            VALUES (?, ?, ?)
        """,
            (case_id, document_id, datetime.now().isoformat()),
        )
        connection.commit()


# ---------------------
# Chunk functions
# ---------------------


def get_chunks_by_document(document_id: str) -> List[Dict[str, Any]]:
    """Get all chunks for a document."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, document_id, page, context, bbox, created_at
            FROM Chunks
            WHERE document_id = ?
            ORDER BY page, id
        """,
            (document_id,),
        )

        chunks = []
        for row in cursor.fetchall():
            chunk = dict(row)
            # Parse bbox JSON
            chunk["bbox"] = json.loads(chunk["bbox"])
            chunks.append(chunk)

        return chunks


def get_chunk_by_id(chunk_id: str) -> Optional[Dict[str, Any]]:
    """Get a chunk by ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, document_id, page, context, bbox, created_at
            FROM Chunks
            WHERE id = ?
        """,
            (chunk_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        chunk = dict(row)
        chunk["bbox"] = json.loads(chunk["bbox"])
        return chunk


def create_chunk(chunk: Dict[str, Any]) -> None:
    """Create a new chunk."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO Chunks (id, document_id, page, context, bbox, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                chunk["id"],
                chunk["document_id"],
                chunk["page"],
                chunk["context"],
                json.dumps(chunk["bbox"]),
                chunk["created_at"],
            ),
        )
        connection.commit()


# ---------------------
# Stakeholder functions
# ---------------------


def get_stakeholders() -> List[Dict[str, Any]]:
    """Get all stakeholders."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, type, name, contact_info, created_at, updated_at
            FROM Stakeholders
            ORDER BY name ASC
        """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_stakeholder_by_id(stakeholder_id: str) -> Optional[Dict[str, Any]]:
    """Get a stakeholder by ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, type, name, contact_info, created_at, updated_at
            FROM Stakeholders
            WHERE id = ?
        """,
            (stakeholder_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_stakeholder(stakeholder: Dict[str, Any]) -> None:
    """Create a new stakeholder."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO Stakeholders (id, type, name, contact_info, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                stakeholder["id"],
                stakeholder.get("type"),
                stakeholder["name"],
                stakeholder.get("contact_info"),
                stakeholder["created_at"],
                stakeholder["updated_at"],
            ),
        )
        connection.commit()


# ---------------------
# Chunk-Stakeholder functions
# ---------------------


def get_chunk_stakeholders(chunk_id: str) -> List[Dict[str, Any]]:
    """Get all stakeholder mentions for a chunk."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT cs.id, cs.chunk_id, cs.stakeholder_id, cs.confidence, cs.mention_text,
                   cs.mention_bbox, cs.verified, cs.created_at,
                   s.type, s.name, s.contact_info
            FROM ChunkStakeholders cs
            JOIN Stakeholders s ON cs.stakeholder_id = s.id
            WHERE cs.chunk_id = ?
            ORDER BY cs.confidence DESC
        """,
            (chunk_id,),
        )

        mentions = []
        for row in cursor.fetchall():
            mention = dict(row)
            mention["mention_bbox"] = json.loads(mention["mention_bbox"])
            mention["verified"] = bool(mention["verified"])
            mentions.append(mention)

        return mentions


def get_stakeholder_mentions_by_document(document_id: str) -> List[Dict[str, Any]]:
    """Get all stakeholder mentions for all chunks in a document."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT cs.id, cs.chunk_id, cs.stakeholder_id, cs.confidence, cs.mention_text,
                   cs.mention_bbox, cs.verified, cs.created_at,
                   s.type, s.name, s.contact_info, s.created_at as stakeholder_created_at,
                   s.updated_at as stakeholder_updated_at
            FROM ChunkStakeholders cs
            JOIN Stakeholders s ON cs.stakeholder_id = s.id
            JOIN Chunks c ON cs.chunk_id = c.id
            WHERE c.document_id = ?
            ORDER BY c.page, cs.confidence DESC
        """,
            (document_id,),
        )

        mentions = []
        for row in cursor.fetchall():
            mention = dict(row)
            mention["mention_bbox"] = json.loads(mention["mention_bbox"])
            mention["verified"] = bool(mention["verified"])
            mentions.append(mention)

        return mentions


def get_case_stakeholders(case_id: str) -> List[Dict[str, Any]]:
    """Get all unique stakeholders for a case (across all documents in the case)."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT DISTINCT 
                s.id, s.type, s.name, s.contact_info, s.created_at, s.updated_at
            FROM Stakeholders s
            JOIN ChunkStakeholders cs ON s.id = cs.stakeholder_id
            JOIN Chunks c ON cs.chunk_id = c.id
            JOIN CaseDocuments cd ON c.document_id = cd.document_id
            WHERE cd.case_id = ?
            ORDER BY s.name ASC
        """,
            (case_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def create_chunk_stakeholder(chunk_stakeholder: Dict[str, Any]) -> None:
    """Create a new chunk-stakeholder relationship."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO ChunkStakeholders (id, chunk_id, stakeholder_id, confidence, mention_text, mention_bbox, verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                chunk_stakeholder["id"],
                chunk_stakeholder["chunk_id"],
                chunk_stakeholder["stakeholder_id"],
                chunk_stakeholder["confidence"],
                chunk_stakeholder["mention_text"],
                json.dumps(chunk_stakeholder["mention_bbox"]),
                1 if chunk_stakeholder.get("verified", False) else 0,
                chunk_stakeholder["created_at"],
            ),
        )
        connection.commit()
