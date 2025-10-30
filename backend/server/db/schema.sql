-- ====================
-- DatabaseSchema for WOO hackathon containing the following tables:
-- - Users
-- - Workspaces
-- - WorkspaceMembers
-- - Cases
-- - Documents
-- - Stakeholders
-- - Chunks
-- - ChunkStakeholders
-- ====================

PRAGMA foreign_keys = ON;

-- ====================
-- Table: Users
-- ====================
CREATE TABLE IF NOT EXISTS Users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT,
    avatar TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ====================
-- Table: Workspaces
-- ====================
CREATE TABLE IF NOT EXISTS Workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES Users(id)
);

-- ====================
-- Table: WorkspaceMembers
-- ====================
CREATE TABLE IF NOT EXISTS WorkspaceMembers (
    workspace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    is_owner INTEGER DEFAULT 0,
    joined_at TEXT NOT NULL,
    PRIMARY KEY (workspace_id, user_id),
    FOREIGN KEY (workspace_id) REFERENCES Workspaces(id),
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

-- ====================
-- Table: Cases
-- ====================
CREATE TABLE IF NOT EXISTS Cases (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    password TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ====================
-- Table: CaseDocuments
-- ====================
CREATE TABLE IF NOT EXISTS CaseDocuments (
    case_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    added_at TEXT NOT NULL,
    PRIMARY KEY (case_id, document_id),
    FOREIGN KEY (case_id) REFERENCES Cases(id),
    FOREIGN KEY (document_id) REFERENCES Documents(id)
);

-- ====================
-- Table: Documents
-- ====================
CREATE TABLE IF NOT EXISTS Documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT,
    file_path TEXT,
    file_size INTEGER,
    page_count INTEGER,
    processing_status TEXT,
    uploaded_at TEXT,
    processed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ====================
-- Table: Stakeholders
-- ====================
CREATE TABLE IF NOT EXISTS Stakeholders (
    id TEXT PRIMARY KEY,
    type TEXT,
    name TEXT NOT NULL,
    contact_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ====================
-- Table: Chunks
-- ====================
CREATE TABLE IF NOT EXISTS Chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page INTEGER NOT NULL,
    context TEXT NOT NULL,
    bbox TEXT NOT NULL, -- JSON: {"x": 0, "y": 0, "width": 100, "height": 200}
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES Documents(id)
);

-- ====================
-- Table: ChunkStakeholders
-- ====================
CREATE TABLE IF NOT EXISTS ChunkStakeholders (
    id TEXT PRIMARY KEY,
    chunk_id TEXT NOT NULL,
    stakeholder_id TEXT NOT NULL,
    confidence REAL NOT NULL,
    mention_text TEXT NOT NULL,
    mention_bbox TEXT NOT NULL, -- JSON: {"x": 0, "y": 0, "width": 100, "height": 12}
    verified INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chunk_id) REFERENCES Chunks(id),
    FOREIGN KEY (stakeholder_id) REFERENCES Stakeholders(id)
);

-- ====================
-- Indexes for performance
-- ====================
CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON WorkspaceMembers(user_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace ON WorkspaceMembers(workspace_id);
CREATE INDEX IF NOT EXISTS idx_case_documents_case ON CaseDocuments(case_id);
CREATE INDEX IF NOT EXISTS idx_case_documents_document ON CaseDocuments(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON Chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunk_stakeholders_chunk ON ChunkStakeholders(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_stakeholders_stakeholder ON ChunkStakeholders(stakeholder_id);
