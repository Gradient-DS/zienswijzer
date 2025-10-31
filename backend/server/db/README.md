# Database Module

This directory contains the database schema, initialization, and helper functions for the WOO application.

## Files

- `schema.sql` - Database schema definition (auto-applied on startup)
- `database.py` - Database connection and helper query functions
- `database.sqlite3` - SQLite database file (created automatically)
- `seed_dummy_data.py` - Script to populate database with test data matching app.py dummy data
- `__init__.py` - Module exports

## Quick Start

### 1. Seed the Database with Dummy Data

From the `WOO/backend/server/db/` directory:

```bash
python seed_dummy_data.py
```

This will create all the dummy data that matches the `DUMMY_*` variables in `app.py`:

- **3 Users**: johndoe, janedoe, bobsmith
- **2 Workspaces**: Project Alpha, Design Team
- **2 Documents**: Email Document, Document PDF
- **4 Stakeholders**: Environmental Agency, Local Council, Community Group A, Business Association B
- **4 Chunks**: Text excerpts from documents with bounding boxes
- **7 Chunk-Stakeholder Relationships**: Stakeholder mentions in chunks with confidence scores
- **3 Cases**: Environmental Impact Study, Community Infrastructure Planning, Urban Development Proposal

### 2. Use Database Functions in Your Code

```python
from . import db

# Example 1: Get all users
users = db.get_users()
print(users)

# Example 2 Get chunks for a document
from db import get_chunks_by_document
chunks = get_chunks_by_document("doc_1")

# Example 3: Get stakeholder mentions for a chunk
from db import get_chunk_stakeholders
mentions = get_chunk_stakeholders("chunk_1")
```

## Available Helper Functions

### Database Management
- `init_db()` - Initialize database with schema (called automatically on app startup)
- `get_connection()` - Get database connection with proper settings

### User Functions
- `get_users()` - Get all users
- `get_user_by_id(user_id: str)` - Get user by ID
- `get_user_by_email(email: str)` - Get user by email
- `get_user_by_username(username: str)` - Get user by username

### Workspace Functions
- `get_workspaces(user_id: Optional[str] = None)` - Get all workspaces, optionally filtered by user
- `get_workspace_by_id(workspace_id: str)` - Get specific workspace with member count
- `get_workspace_members(workspace_id: str)` - Get all members of a workspace
- `create_workspace(workspace: Dict[str, Any])` - Create a new workspace with members

### Case Functions
- `get_cases()` - Get all cases with their document IDs
- `get_case_by_id(case_id: str)` - Get specific case with document IDs
- `create_case(case: Dict[str, Any])` - Create a new case

### Document Functions
- `get_documents()` - Get all documents
- `get_document_by_id(doc_id: str)` - Get specific document
- `create_document(document: Dict[str, Any])` - Create a new document
- `add_document_to_case(case_id: str, document_id: str)` - Link a document to a case

### Chunk Functions
- `get_chunks_by_document(document_id: str)` - Get all chunks for a document (with parsed bbox)
- `get_chunk_by_id(chunk_id: str)` - Get specific chunk

### Stakeholder Functions
- `get_stakeholders()` - Get all stakeholders
- `get_stakeholder_by_id(stakeholder_id: str)` - Get specific stakeholder

### Chunk-Stakeholder Functions
- `get_chunk_stakeholders(chunk_id: str)` - Get all stakeholder mentions for a chunk (includes stakeholder info)
- `get_stakeholder_mentions_by_document(document_id: str)` - Get all stakeholder mentions in a document

### OAuth Token Functions
- `get_oauth_token(user_id: str)` - Get OAuth token for a user
- `save_oauth_token(user_id: str, access_token: str, refresh_token: Optional[str], expires_at: float)` - Save or update OAuth token
- `delete_oauth_token(user_id: str)` - Delete OAuth token for a user

## Database Schema

The database uses the following tables:

### Users
Stores user accounts with authentication info.
- `id` (TEXT, PK)
- `username` (TEXT, UNIQUE)
- `email` (TEXT, UNIQUE)
- `password` (TEXT)
- `avatar` (TEXT) - URL to avatar image
- `created_at`, `updated_at` (TEXT) - ISO timestamps

### Workspaces
Collaborative workspaces for organizing work.
- `id` (TEXT, PK)
- `name` (TEXT)
- `description` (TEXT)
- `owner_id` (TEXT, FK → Users)
- `created_at`, `updated_at` (TEXT)

### WorkspaceMembers
Many-to-many relationship between workspaces and users.
- `workspace_id` (TEXT, FK → Workspaces)
- `user_id` (TEXT, FK → Users)
- `is_owner` (INTEGER) - Boolean flag
- `joined_at` (TEXT)

### Cases
WOO (Wet Open Overheid) cases/requests.
- `id` (TEXT, PK)
- `title` (TEXT)
- `description` (TEXT)
- `password` (TEXT) - Optional password protection
- `created_at`, `updated_at` (TEXT)

### CaseDocuments
Links cases to their documents.
- `case_id` (TEXT, FK → Cases)
- `document_id` (TEXT, FK → Documents)
- `added_at` (TEXT)

### Documents
PDF documents and their metadata.
- `id` (TEXT, PK)
- `title` (TEXT)
- `description` (TEXT)
- `type` (TEXT) - e.g., "email", "document"
- `file_path` (TEXT) - Path to PDF file
- `file_size` (INTEGER) - Size in bytes
- `page_count` (INTEGER)
- `processing_status` (TEXT) - e.g., "completed", "processing"
- `uploaded_at`, `processed_at` (TEXT)
- `created_at`, `updated_at` (TEXT)

### Stakeholders
Organizations, government bodies, or community groups.
- `id` (TEXT, PK)
- `type` (TEXT) - e.g., "organization", "government", "community"
- `name` (TEXT)
- `contact_info` (TEXT)
- `created_at`, `updated_at` (TEXT)

### Chunks
Text excerpts from documents with position info.
- `id` (TEXT, PK)
- `document_id` (TEXT, FK → Documents)
- `page` (INTEGER)
- `context` (TEXT) - The actual text content
- `bbox` (TEXT) - JSON: `{"x": 0, "y": 0, "width": 100, "height": 200}`
- `created_at` (TEXT)

### ChunkStakeholders
Stakeholder mentions detected in chunks (NER results).
- `id` (TEXT, PK)
- `chunk_id` (TEXT, FK → Chunks)
- `stakeholder_id` (TEXT, FK → Stakeholders)
- `confidence` (REAL) - 0.0 to 1.0
- `mention_text` (TEXT) - The actual text that mentions the stakeholder
- `mention_bbox` (TEXT) - JSON: bounding box of the mention
- `verified` (INTEGER) - Boolean: has the mention been verified?
- `created_at` (TEXT)

### OAuthTokens
OAuth tokens for email integration (Microsoft Graph API).
- `user_id` (TEXT, PK) - User identifier (no FK constraint for flexibility)
- `access_token` (TEXT) - OAuth access token
- `refresh_token` (TEXT) - OAuth refresh token
- `expires_at` (REAL) - Unix timestamp when token expires
- `created_at` (TEXT)
- `updated_at` (TEXT)

**Note:** No foreign key constraint to Users table to allow the email module to work independently with any user_id string.

## Notes

- All timestamps are in ISO 8601 format with 'Z' suffix (UTC)
- Bounding boxes are stored as JSON strings and parsed automatically by helper functions
- The database schema matches the structure used in the FastAPI application
- `init_db()` is called automatically on FastAPI startup, so you don't need to manually initialize the database
- Create functions (`create_case`, `create_document`, `create_workspace`) handle database inserts and commits
- All get functions return dictionaries with snake_case keys - API layer converts to camelCase
