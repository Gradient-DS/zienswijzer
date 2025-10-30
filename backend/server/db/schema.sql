-- ====================
-- DatabaseSchema for WOO hackathon containing the following tables:
-- - Users
-- - WOO_Case
-- - Document
-- - Stakeholders
-- - Chunks
-- - Issues
-- ====================

PRAGMA foreign_keys = ON;

-- ====================
-- Table: Users
-- ====================
CREATE TABLE IF NOT EXISTS Users (
    uuid INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    name TEXT,
    picture BLOB,
    role TEXT
);

-- ====================
-- Table: WOO_Case
-- ====================
CREATE TABLE IF NOT EXISTS WOO_Case (
    uuid INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    password TEXT,
    requester TEXT,
    document_IDs TEXT, -- JSON list of document UUIDs
    FOREIGN KEY (requester) REFERENCES Users(email)
);

-- ====================
-- Table: Document
-- ====================
CREATE TABLE IF NOT EXISTS Document (
    uuid INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT
);

-- ====================
-- Table: Stakeholders
-- ====================
CREATE TABLE IF NOT EXISTS Stakeholders (
    uuid INTEGER PRIMARY KEY,
    type TEXT,
    name TEXT,
    contact_info TEXT
);

-- ====================
-- Table: Chunks
-- ====================
CREATE TABLE IF NOT EXISTS Chunks (
    uuid INTEGER PRIMARY KEY,
    document_ID INTEGER NOT NULL,
    stakeholder_IDs TEXT, -- JSON list of stakeholder UUIDs
    page INTEGER,
    context TEXT,
    bbox TEXT, -- e.g. JSON: {"x":0,"y":0,"w":100,"h":200}
    FOREIGN KEY (document_ID) REFERENCES Document(uuid)
);

-- ====================
-- Table: Issues
-- ====================
CREATE TABLE IF NOT EXISTS Issues (
    uuid INTEGER PRIMARY KEY,
    chunk_ID INTEGER NOT NULL,
    stakeholder_ID INTEGER NOT NULL,
    FOREIGN KEY (chunk_ID) REFERENCES Chunks(uuid),
    FOREIGN KEY (stakeholder_ID) REFERENCES Stakeholders(uuid)
);
