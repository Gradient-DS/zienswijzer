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
    updated_at TEXT NOT NULL,
    document_ids TEXT[]
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
    keywords TEXT,
    author TEXT,
    file_path TEXT,
    file_size INTEGER,
    page_count INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    parse_status TEXT
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
-- Table: OAuthTokens
-- ====================
CREATE TABLE IF NOT EXISTS OAuthTokens (
    user_id TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ====================
-- Table: SentEmails
-- ====================
CREATE TABLE IF NOT EXISTS SentEmails (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    body_type TEXT DEFAULT 'HTML',
    to_recipients TEXT NOT NULL, -- JSON array: [{"address": "...", "name": "..."}]
    cc_recipients TEXT, -- JSON array
    bcc_recipients TEXT, -- JSON array
    importance TEXT DEFAULT 'normal',
    outlook_message_id TEXT, -- Message ID from Outlook (if available)
    outlook_conversation_id TEXT, -- Conversation ID from Outlook for threading
    tracking_id TEXT, -- Unique tracking ID added to email subject for reply detection
    sent_at TEXT NOT NULL,
    case_id TEXT, -- Optional link to a case
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES Cases(id)
);

-- ====================
-- Table: EmailReplies
-- ====================
CREATE TABLE IF NOT EXISTS EmailReplies (
    id TEXT PRIMARY KEY,
    sent_email_id TEXT NOT NULL,
    outlook_message_id TEXT NOT NULL UNIQUE, -- Message ID from Outlook
    from_address TEXT NOT NULL, -- JSON: {"address": "...", "name": "..."}
    subject TEXT NOT NULL,
    body_preview TEXT,
    body TEXT,
    body_type TEXT DEFAULT 'HTML',
    received_at TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    has_attachments INTEGER DEFAULT 0,
    importance TEXT DEFAULT 'normal',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (sent_email_id) REFERENCES SentEmails(id)
);

-- ====================
-- Table: CaseChunkStakeholderVerification
-- ====================
CREATE TABLE IF NOT EXISTS CaseChunkStakeholderVerification (
    case_id TEXT NOT NULL,
    chunk_stakeholder_id TEXT NOT NULL,
    verified INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (case_id, chunk_stakeholder_id),
    FOREIGN KEY (case_id) REFERENCES Cases(id),
    FOREIGN KEY (chunk_stakeholder_id) REFERENCES ChunkStakeholders(id)
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
CREATE INDEX IF NOT EXISTS idx_case_verification_case ON CaseChunkStakeholderVerification(case_id);
CREATE INDEX IF NOT EXISTS idx_case_verification_mention ON CaseChunkStakeholderVerification(chunk_stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_expires_at ON OAuthTokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_sent_emails_user ON SentEmails(user_id);
CREATE INDEX IF NOT EXISTS idx_sent_emails_case ON SentEmails(case_id);
CREATE INDEX IF NOT EXISTS idx_sent_emails_sent_at ON SentEmails(sent_at);
CREATE INDEX IF NOT EXISTS idx_sent_emails_conversation ON SentEmails(outlook_conversation_id);
CREATE INDEX IF NOT EXISTS idx_email_replies_sent_email ON EmailReplies(sent_email_id);
CREATE INDEX IF NOT EXISTS idx_email_replies_outlook_message ON EmailReplies(outlook_message_id);
CREATE INDEX IF NOT EXISTS idx_email_replies_received_at ON EmailReplies(received_at);
