"""
Seed script to populate the database with dummy data.

Usage:
    python seed_dummy_data.py
"""

import json
from database import init_db, get_connection


def seed_database():
    """Populate the database with dummy data for testing."""
    
    # Initialize the database first
    init_db()
    print("✅ Database initialized")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Create a fake user
        cursor.execute("""
            INSERT INTO Users (email, password, name, role)
            VALUES (?, ?, ?, ?)
        """, (
            "jan.vries@example.nl",
            "securepassword123",  # In production, use hashed passwords!
            "Jan de Vries",
            "citizen"
        ))
        user_id = cursor.lastrowid
        print(f"✅ Created user: Jan de Vries (ID: {user_id})")
        
        # 2. Create two documents
        cursor.execute("""
            INSERT INTO Document (title, description, type)
            VALUES (?, ?, ?)
        """, (
            "Gemeentelijke Begroting 2024",
            "Officiële begroting van de gemeente Amsterdam voor het jaar 2024, inclusief infrastructuurprojecten en sociale voorzieningen.",
            "PDF"
        ))
        doc1_id = cursor.lastrowid
        print(f"✅ Created document: Gemeentelijke Begroting 2024 (ID: {doc1_id})")
        
        cursor.execute("""
            INSERT INTO Document (title, description, type)
            VALUES (?, ?, ?)
        """, (
            "Vergunningsaanvraag Nieuwbouw Centrum",
            "Vergunningsaanvraag en bijbehorende documenten voor nieuwbouwproject in het stadscentrum.",
            "PDF"
        ))
        doc2_id = cursor.lastrowid
        print(f"✅ Created document: Vergunningsaanvraag Nieuwbouw Centrum (ID: {doc2_id})")
        
        # 3. Create a WOO case/request linking user and documents
        document_ids_json = json.dumps([doc1_id, doc2_id])
        cursor.execute("""
            INSERT INTO WOO_Case (title, description, password, requester, document_IDs)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "WOO-verzoek: Begroting en Bouwplannen 2024",
            "Verzoek om openbaarmaking van gemeentelijke begrotingsstukken en vergunningsaanvragen voor nieuwbouwprojecten in het centrum volgens de Wet Open Overheid.",
            None,  # No password protection
            "jan.vries@example.nl",
            document_ids_json
        ))
        case_id = cursor.lastrowid
        print(f"✅ Created WOO case: WOO-verzoek: Begroting en Bouwplannen 2024 (ID: {case_id})")
        
        # 4. Create some stakeholders
        cursor.execute("""
            INSERT INTO Stakeholders (type, name, contact_info)
            VALUES (?, ?, ?)
        """, (
            "organization",
            "Gemeente Amsterdam",
            "info@amsterdam.nl"
        ))
        stakeholder1_id = cursor.lastrowid
        print(f"✅ Created stakeholder: Gemeente Amsterdam (ID: {stakeholder1_id})")
        
        cursor.execute("""
            INSERT INTO Stakeholders (type, name, contact_info)
            VALUES (?, ?, ?)
        """, (
            "organization",
            "Bouwbedrijf De Constructie BV",
            "contact@deconstructie.nl"
        ))
        stakeholder2_id = cursor.lastrowid
        print(f"✅ Created stakeholder: Bouwbedrijf De Constructie BV (ID: {stakeholder2_id})")
        
        # 5. Create some chunks for the documents
        cursor.execute("""
            INSERT INTO Chunks (document_ID, stakeholder_IDs, page, context, bbox)
            VALUES (?, ?, ?, ?, ?)
        """, (
            doc1_id,
            json.dumps([stakeholder1_id]),
            5,
            "Budget voor infrastructuur: €2.5 miljoen gealloceerd voor renovatie van de hoofdstraat.",
            json.dumps({"x": 50, "y": 100, "w": 400, "h": 80})
        ))
        chunk1_id = cursor.lastrowid
        print(f"✅ Created chunk for document {doc1_id} (Chunk ID: {chunk1_id})")
        
        cursor.execute("""
            INSERT INTO Chunks (document_ID, stakeholder_IDs, page, context, bbox)
            VALUES (?, ?, ?, ?, ?)
        """, (
            doc2_id,
            json.dumps([stakeholder1_id, stakeholder2_id]),
            2,
            "De aanvrager Bouwbedrijf De Constructie BV heeft toestemming gevraagd voor een gebouw van 12 verdiepingen.",
            json.dumps({"x": 50, "y": 200, "w": 450, "h": 100})
        ))
        chunk2_id = cursor.lastrowid
        print(f"✅ Created chunk for document {doc2_id} (Chunk ID: {chunk2_id})")
        
        # 6. Create an issue linking a chunk to a stakeholder
        cursor.execute("""
            INSERT INTO Issues (chunk_ID, stakeholder_ID)
            VALUES (?, ?)
        """, (
            chunk2_id,
            stakeholder2_id
        ))
        issue_id = cursor.lastrowid
        print(f"✅ Created issue linking chunk {chunk2_id} to stakeholder {stakeholder2_id} (Issue ID: {issue_id})")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 All dummy data successfully seeded!")
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY OF DUMMY DATA")
        print("="*60)
        print(f"User: Jan de Vries (jan.vries@example.nl)")
        print(f"WOO Case: WOO-verzoek: Begroting en Bouwplannen 2024")
        print(f"Documents: 2 documents created")
        print(f"  - Gemeentelijke Begroting 2024")
        print(f"  - Vergunningsaanvraag Nieuwbouw Centrum")
        print(f"Stakeholders: 2 stakeholders created")
        print(f"Chunks: 2 chunks created")
        print(f"Issues: 1 issue created")
        print("="*60)
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()

