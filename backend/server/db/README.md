# Database Module

This directory contains the database schema, initialization, and helper functions for the WOO application.

## Files

- `schema.sql` - Database schema definition
- `database.py` - Database connection and helper functions
- `database.sqlite3` - SQLite database file (created on first run)
- `seed_dummy_data.py` - Script to populate database with test data
- `create_db.py` - Legacy script (can be removed, replaced by `init_db()`)

## Quick Start

### 1. Seed the Database with Dummy Data

From the `WOO/backend/server/db/` directory:

```bash
python seed_dummy_data.py
```

This will create:
- **1 User**: Jan de Vries (jan.vries@example.nl)
- **1 WOO Case**: Request for budget and building plans
- **2 Documents**: 
  - Gemeentelijke Begroting 2024
  - Vergunningsaanvraag Nieuwbouw Centrum
- **2 Stakeholders**: Municipality and construction company
- **2 Chunks**: Text excerpts from the documents
- **1 Issue**: Linking a chunk to a stakeholder

### 2. Use Database Functions in Your Code

```python
from db import (
    get_users,
    get_woo_cases,
    get_documents,
    get_user_by_email,
    create_user,
)

# Get all users
users = get_users()
print(users)

# Get all WOO cases
cases = get_woo_cases()
print(cases)

# Get all documents
documents = get_documents()
print(documents)

# Get specific user
user = get_user_by_email("jan.vries@example.nl")
print(user)
```

## Available Helper Functions

### User Functions
- `get_users()` - Get all users
- `get_user_by_email(email: str)` - Get user by email
- `create_user(email, password, name=None, role=None, picture=None)` - Create new user

### WOO Case Functions
- `get_woo_cases()` - Get all WOO cases
- `get_woo_case_by_id(case_id: int)` - Get specific case

### Document Functions
- `get_documents()` - Get all documents
- `get_document_by_id(doc_id: int)` - Get specific document

### Stakeholder Functions
- `get_stakeholders()` - Get all stakeholders

### Database Management
- `init_db()` - Initialize database with schema
- `get_connection()` - Get database connection with proper settings

## Database Schema

See `schema.sql` for the complete schema. Main tables:
- **Users** - User accounts
- **WOO_Case** - WOO requests/cases
- **Document** - Documents related to cases
- **Stakeholders** - Organizations/people involved
- **Chunks** - Text excerpts from documents
- **Issues** - Links between chunks and stakeholders

