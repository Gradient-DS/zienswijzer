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
    update_document,
    # Chunk functions
    get_chunks_by_document,
    get_chunk_by_id,
    create_chunk,
    # Stakeholder functions
    get_stakeholders,
    get_stakeholder_by_id,
    create_stakeholder,
    # Chunk-Stakeholder functions
    get_chunk_stakeholders,
    get_stakeholder_mentions_by_document,
<<<<<<< HEAD
    # OAuth Token functions
    get_oauth_token,
    save_oauth_token,
    delete_oauth_token,
    # Sent Email functions
    save_sent_email,
    get_sent_emails,
    get_sent_email_by_id,
    get_sent_email_by_conversation_id,
    # Email Reply functions
    save_email_reply,
    get_email_replies,
    get_email_reply_by_outlook_id,
=======
    create_chunk_stakeholder,
>>>>>>> main
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
    "update_document",
    # Chunk functions
    "get_chunks_by_document",
    "get_chunk_by_id",
    "create_chunk",
    # Stakeholder functions
    "get_stakeholders",
    "get_stakeholder_by_id",
    "create_stakeholder",
    # Chunk-Stakeholder functions
    "get_chunk_stakeholders",
    "get_stakeholder_mentions_by_document",
<<<<<<< HEAD
    # OAuth Token functions
    "get_oauth_token",
    "save_oauth_token",
    "delete_oauth_token",
    # Sent Email functions
    "save_sent_email",
    "get_sent_emails",
    "get_sent_email_by_id",
    "get_sent_email_by_conversation_id",
    # Email Reply functions
    "save_email_reply",
    "get_email_replies",
    "get_email_reply_by_outlook_id",
=======
    "create_chunk_stakeholder",
>>>>>>> main
]
