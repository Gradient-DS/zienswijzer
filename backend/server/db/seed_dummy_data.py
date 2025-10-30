"""
Seed script to populate the database with dummy data.

Usage:
    python seed_dummy_data.py
"""

import json
from database import init_db, get_connection

# Dummy data matching app.py structure
DUMMY_USERS = [
    {
        "id": "user_1",
        "username": "johndoe",
        "email": "john.doe@example.com",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=john",
    },
    {
        "id": "user_2",
        "username": "janedoe",
        "email": "jane.doe@example.com",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=jane",
    },
    {
        "id": "user_3",
        "username": "bobsmith",
        "email": "bob.smith@example.com",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=bob",
    },
]

DUMMY_WORKSPACES = [
    {
        "id": "workspace_1",
        "name": "Project Alpha",
        "description": "Main development workspace for Alpha project",
        "createdAt": "2024-01-15T10:00:00Z",
        "updatedAt": "2024-01-20T15:30:00Z",
        "memberCount": 3,
        "isOwner": True,
        "ownerId": "user_1",
    },
    {
        "id": "workspace_2",
        "name": "Design Team",
        "description": "UI/UX design collaboration space",
        "createdAt": "2024-01-10T09:00:00Z",
        "updatedAt": "2024-01-18T11:45:00Z",
        "memberCount": 5,
        "isOwner": False,
        "ownerId": "user_2",
    },
]

DUMMY_DOCUMENTS = [
    {
        "id": "doc_1",
        "title": "Email Document",
        "description": "Sample email document for testing",
        "type": "email",
        "filePath": "data/email.pdf",
        "fileSize": 102400,
        "pageCount": 2,
        "processingStatus": "completed",
        "uploadedAt": "2024-01-16T14:00:00Z",
        "processedAt": "2024-01-16T14:05:00Z",
        "createdAt": "2024-01-16T14:00:00Z",
        "updatedAt": "2024-01-20T10:30:00Z",
    },
    {
        "id": "doc_2",
        "title": "Document PDF",
        "description": "Sample document PDF for testing",
        "type": "document",
        "filePath": "data/document.pdf",
        "fileSize": 204800,
        "pageCount": 5,
        "processingStatus": "completed",
        "uploadedAt": "2024-01-18T09:15:00Z",
        "processedAt": "2024-01-18T09:20:00Z",
        "createdAt": "2024-01-18T09:15:00Z",
        "updatedAt": "2024-01-19T16:45:00Z",
    },
]

DUMMY_CHUNKS = [
    {
        "id": "chunk_1",
        "documentId": "doc_1",
        "page": 1,
        "context": "Dear Environmental Agency, We are writing to inform you about the proposed development project in the Utrecht peat meadow area. Local Council has requested a comprehensive environmental impact assessment.",
        "bbox": {"x": 100, "y": 200, "width": 400, "height": 150},
    },
    {
        "id": "chunk_2",
        "documentId": "doc_1",
        "page": 1,
        "context": "The project will require consultation with Community Group A and Business Association B. We need to schedule meetings with all stakeholders to discuss the potential impacts.",
        "bbox": {"x": 100, "y": 400, "width": 400, "height": 120},
    },
    {
        "id": "chunk_3",
        "documentId": "doc_2",
        "page": 1,
        "context": "The Environmental Agency has raised concerns about wildlife habitat impact. Local Council must approve the proposal before any construction can begin.",
        "bbox": {"x": 80, "y": 150, "width": 450, "height": 100},
    },
    {
        "id": "chunk_4",
        "documentId": "doc_2",
        "page": 2,
        "context": "Community Group A has submitted feedback regarding the proposed changes. We need to review their concerns and respond accordingly.",
        "bbox": {"x": 90, "y": 300, "width": 420, "height": 110},
    },
]

DUMMY_STAKEHOLDERS = [
    {
        "id": "stakeholder_1",
        "type": "organization",
        "name": "Environmental Agency",
        "contactInfo": "contact@environmental-agency.gov.nl",
        "createdAt": "2024-01-10T08:00:00Z",
        "updatedAt": "2024-01-10T08:00:00Z",
    },
    {
        "id": "stakeholder_2",
        "type": "government",
        "name": "Local Council",
        "contactInfo": "info@localcouncil.nl",
        "createdAt": "2024-01-11T10:00:00Z",
        "updatedAt": "2024-01-11T10:00:00Z",
    },
    {
        "id": "stakeholder_3",
        "type": "community",
        "name": "Community Group A",
        "contactInfo": "contact@communitygroupa.org",
        "createdAt": "2024-01-12T09:00:00Z",
        "updatedAt": "2024-01-12T09:00:00Z",
    },
    {
        "id": "stakeholder_4",
        "type": "organization",
        "name": "Business Association B",
        "contactInfo": "info@businessassocb.nl",
        "createdAt": "2024-01-13T11:00:00Z",
        "updatedAt": "2024-01-13T11:00:00Z",
    },
]

DUMMY_CHUNK_STAKEHOLDERS = [
    {
        "id": "cs_1",
        "chunkId": "chunk_1",
        "stakeholderId": "stakeholder_1",
        "confidence": 0.95,
        "mentionText": "Environmental Agency",
        "mentionBbox": {"x": 105, "y": 205, "width": 120, "height": 12},
        "verified": True,
        "createdAt": "2024-01-20T10:00:00Z",
    },
    {
        "id": "cs_2",
        "chunkId": "chunk_1",
        "stakeholderId": "stakeholder_2",
        "confidence": 0.92,
        "mentionText": "Local Council",
        "mentionBbox": {"x": 390, "y": 205, "width": 90, "height": 12},
        "verified": True,
        "createdAt": "2024-01-20T10:00:00Z",
    },
    {
        "id": "cs_3",
        "chunkId": "chunk_2",
        "stakeholderId": "stakeholder_3",
        "confidence": 0.88,
        "mentionText": "Community Group A",
        "mentionBbox": {"x": 250, "y": 405, "width": 110, "height": 12},
        "verified": False,
        "createdAt": "2024-01-20T10:05:00Z",
    },
    {
        "id": "cs_4",
        "chunkId": "chunk_2",
        "stakeholderId": "stakeholder_4",
        "confidence": 0.85,
        "mentionText": "Business Association B",
        "mentionBbox": {"x": 110, "y": 430, "width": 140, "height": 12},
        "verified": False,
        "createdAt": "2024-01-20T10:05:00Z",
    },
    {
        "id": "cs_5",
        "chunkId": "chunk_3",
        "stakeholderId": "stakeholder_1",
        "confidence": 0.93,
        "mentionText": "Environmental Agency",
        "mentionBbox": {"x": 85, "y": 155, "width": 120, "height": 12},
        "verified": True,
        "createdAt": "2024-01-20T10:10:00Z",
    },
    {
        "id": "cs_6",
        "chunkId": "chunk_3",
        "stakeholderId": "stakeholder_2",
        "confidence": 0.90,
        "mentionText": "Local Council",
        "mentionBbox": {"x": 370, "y": 155, "width": 90, "height": 12},
        "verified": True,
        "createdAt": "2024-01-20T10:10:00Z",
    },
    {
        "id": "cs_7",
        "chunkId": "chunk_4",
        "stakeholderId": "stakeholder_3",
        "confidence": 0.87,
        "mentionText": "Community Group A",
        "mentionBbox": {"x": 95, "y": 305, "width": 110, "height": 12},
        "verified": False,
        "createdAt": "2024-01-20T10:15:00Z",
    },
]

DUMMY_CASES = [
    {
        "id": "case_1",
        "title": "Environmental Impact Study",
        "description": "Comprehensive environmental assessment for new development",
        "documentIds": ["doc_1", "doc_2"],
        "createdAt": "2024-01-15T10:00:00Z",
        "updatedAt": "2024-01-20T15:30:00Z",
    },
    {
        "id": "case_2",
        "title": "Community Infrastructure Planning",
        "description": "Planning documentation for community infrastructure projects",
        "documentIds": ["doc_1"],
        "createdAt": "2024-01-10T09:00:00Z",
        "updatedAt": "2024-01-18T11:45:00Z",
    },
    {
        "id": "case_3",
        "title": "Urban Development Proposal",
        "description": "Proposal for urban development in central district",
        "documentIds": [],
        "createdAt": "2024-01-22T08:00:00Z",
        "updatedAt": "2024-01-22T08:00:00Z",
    },
]


def seed_database():
    """Populate the database with dummy data for testing."""
    
    # Initialize the database first
    init_db()
    print("[OK] Database initialized")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Create users
        print("\n[SEEDING] Users...")
        for user in DUMMY_USERS:
            cursor.execute("""
                INSERT INTO Users (id, username, email, password, avatar, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user["id"],
                user["username"],
                user["email"],
                "password123",  # Default password for all users
                user["avatar"],
                "2024-01-01T00:00:00Z",
                "2024-01-01T00:00:00Z",
            ))
            print(f"  [+] {user['username']} ({user['email']})")
        
        # 2. Create workspaces
        print("\n[SEEDING] Workspaces...")
        for workspace in DUMMY_WORKSPACES:
            cursor.execute("""
                INSERT INTO Workspaces (id, name, description, created_at, updated_at, owner_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                workspace["id"],
                workspace["name"],
                workspace["description"],
                workspace["createdAt"],
                workspace["updatedAt"],
                workspace["ownerId"],
            ))
            print(f"  [+] {workspace['name']}")
            
            # Add workspace members
            member_count = workspace["memberCount"]
            for i in range(min(member_count, len(DUMMY_USERS))):
                user_id = DUMMY_USERS[i]["id"]
                is_owner = 1 if user_id == workspace["ownerId"] else 0
                cursor.execute("""
                    INSERT INTO WorkspaceMembers (workspace_id, user_id, is_owner, joined_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    workspace["id"],
                    user_id,
                    is_owner,
                    workspace["createdAt"],
                ))
                print(f"    [+] Member: {DUMMY_USERS[i]['username']}")
        
        # 3. Create documents
        print("\n[SEEDING] Documents...")
        for doc in DUMMY_DOCUMENTS:
            cursor.execute("""
                INSERT INTO Documents (
                    id, title, description, type, file_path, file_size, page_count,
                    processing_status, uploaded_at, processed_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["id"],
                doc["title"],
                doc["description"],
                doc["type"],
                doc["filePath"],
                doc["fileSize"],
                doc["pageCount"],
                doc["processingStatus"],
                doc["uploadedAt"],
                doc["processedAt"],
                doc["createdAt"],
                doc["updatedAt"],
            ))
            print(f"  [+] {doc['title']} ({doc['type']})")
        
        # 4. Create stakeholders
        print("\n[SEEDING] Stakeholders...")
        for stakeholder in DUMMY_STAKEHOLDERS:
            cursor.execute("""
                INSERT INTO Stakeholders (id, type, name, contact_info, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                stakeholder["id"],
                stakeholder["type"],
                stakeholder["name"],
                stakeholder["contactInfo"],
                stakeholder["createdAt"],
                stakeholder["updatedAt"],
            ))
            print(f"  [+] {stakeholder['name']} ({stakeholder['type']})")
        
        # 5. Create chunks
        print("\n[SEEDING] Chunks...")
        for chunk in DUMMY_CHUNKS:
            cursor.execute("""
                INSERT INTO Chunks (id, document_id, page, context, bbox, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                chunk["id"],
                chunk["documentId"],
                chunk["page"],
                chunk["context"],
                json.dumps(chunk["bbox"]),
                "2024-01-20T10:00:00Z",
            ))
            print(f"  [+] {chunk['id']} (page {chunk['page']})")
        
        # 6. Create chunk-stakeholder relationships
        print("\n[SEEDING] Chunk-Stakeholder relationships...")
        for cs in DUMMY_CHUNK_STAKEHOLDERS:
            cursor.execute("""
                INSERT INTO ChunkStakeholders (
                    id, chunk_id, stakeholder_id, confidence, mention_text, mention_bbox, verified, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cs["id"],
                cs["chunkId"],
                cs["stakeholderId"],
                cs["confidence"],
                cs["mentionText"],
                json.dumps(cs["mentionBbox"]),
                1 if cs["verified"] else 0,
                cs["createdAt"],
            ))
            print(f"  [+] {cs['id']} ({cs['mentionText']}, confidence: {cs['confidence']:.2f})")
        
        # 7. Create cases
        print("\n[SEEDING] Cases...")
        for case in DUMMY_CASES:
            cursor.execute("""
                INSERT INTO Cases (id, title, description, password, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                case["id"],
                case["title"],
                case["description"],
                None,
                case["createdAt"],
                case["updatedAt"],
            ))
            print(f"  [+] {case['title']}")
            
            # Add case-document relationships
            for doc_id in case["documentIds"]:
                cursor.execute("""
                    INSERT INTO CaseDocuments (case_id, document_id, added_at)
                    VALUES (?, ?, ?)
                """, (
                    case["id"],
                    doc_id,
                    case["createdAt"],
                ))
                print(f"    [+] Document: {doc_id}")
        
        # Commit all changes
        conn.commit()
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY OF DUMMY DATA")
        print("="*60)
        print(f"Users:               {len(DUMMY_USERS)}")
        print(f"Workspaces:          {len(DUMMY_WORKSPACES)}")
        print(f"Documents:           {len(DUMMY_DOCUMENTS)}")
        print(f"Stakeholders:        {len(DUMMY_STAKEHOLDERS)}")
        print(f"Chunks:              {len(DUMMY_CHUNKS)}")
        print(f"Chunk-Stakeholders:  {len(DUMMY_CHUNK_STAKEHOLDERS)}")
        print(f"Cases:               {len(DUMMY_CASES)}")
        print("="*60)
        print("\n[SUCCESS] All dummy data successfully seeded!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Error seeding database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()
