"""WOO Backend Database"""

from .database import (
    init_db,
    get_connection,
    # User functions
    get_users,
    get_user_by_id,
    get_user_by_email,
    get_user_by_username,
    # Workspace functions
    get_workspaces,
    get_workspace_by_id,
    get_workspace_members,
    create_workspace,
    # Case functions
    get_cases,
    get_case_by_id,
    create_case,
    # Document functions
    get_documents,
    get_document_by_id,
    create_document,
    add_document_to_case,
    # Chunk functions
    get_chunks_by_document,
    get_chunk_by_id,
    # Stakeholder functions
    get_stakeholders,
    get_stakeholder_by_id,
    # Chunk-Stakeholder functions
    get_chunk_stakeholders,
    get_stakeholder_mentions_by_document,
    # OAuth Token functions
    get_oauth_token,
    save_oauth_token,
    delete_oauth_token,
)

__all__ = [
    "init_db",
    "get_connection",
    # User functions
    "get_users",
    "get_user_by_id",
    "get_user_by_email",
    "get_user_by_username",
    # Workspace functions
    "get_workspaces",
    "get_workspace_by_id",
    "get_workspace_members",
    "create_workspace",
    # Case functions
    "get_cases",
    "get_case_by_id",
    "create_case",
    # Document functions
    "get_documents",
    "get_document_by_id",
    "create_document",
    "add_document_to_case",
    # Chunk functions
    "get_chunks_by_document",
    "get_chunk_by_id",
    # Stakeholder functions
    "get_stakeholders",
    "get_stakeholder_by_id",
    # Chunk-Stakeholder functions
    "get_chunk_stakeholders",
    "get_stakeholder_mentions_by_document",
    # OAuth Token functions
    "get_oauth_token",
    "save_oauth_token",
    "delete_oauth_token",
]
