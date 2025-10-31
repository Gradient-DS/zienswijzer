from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# from .utils.text_processor import transform_text
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import shutil
import uuid
from server import db
from server.utils.parsing import main as parse_pdf
from server.utils.ner_processor import MarkdownNERProcessor
import random
from server.utils.text_processor import transform_text
from server.utils.chunk_generator import (
    generate_fake_chunks,
    generate_fake_stakeholders,
    generate_fake_chunk_stakeholders,
)
import logging


logging.basicConfig(
    level=getattr(logging, "INFO", logging.INFO),
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="WOO Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


# Pydantic models
class TextInput(BaseModel):
    text: str


class TextOutput(BaseModel):
    original: str
    transformed: str


class LoginRequest(BaseModel):
    username: str
    email: str


class User(BaseModel):
    id: str
    username: str
    email: str
    avatar: Optional[str] = None


class LoginResponse(BaseModel):
    user: User
    token: str


class LogoutResponse(BaseModel):
    success: bool
    message: str


class AuthMeResponse(BaseModel):
    user: User


class Workspace(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    member_count: int
    is_owner: bool


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    page: int


class Document(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: Optional[str] = None
    keywords: Optional[str] = None
    author: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    parse_status: Optional[str] = None


class WorkspaceDetail(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    member_count: int
    is_owner: bool
    members: List[User]
    documents: List[Document]


class CreateWorkspaceRequest(BaseModel):
    name: str
    description: Optional[str] = None


class CreateWorkspaceResponse(BaseModel):
    workspace: Workspace


class WorkspaceListResponse(BaseModel):
    workspaces: List[Workspace]


class WorkspaceDetailResponse(BaseModel):
    workspace: WorkspaceDetail


class Case(BaseModel):
    id: str
    title: str
    description: str
    document_ids: List[str]
    created_at: str
    updated_at: str


class CaseDetail(BaseModel):
    id: str
    title: str
    description: str
    document_ids: List[str]
    created_at: str
    updated_at: str
    documents: List[Document]


class CreateCaseRequest(BaseModel):
    title: str
    description: str
    password: Optional[str] = None


class CreateCaseResponse(BaseModel):
    case: Case


class CaseListResponse(BaseModel):
    cases: List[Case]


class CaseDetailResponse(BaseModel):
    case: CaseDetail


class Stakeholder(BaseModel):
    id: str
    type: Optional[str] = None
    name: str
    contact_info: Optional[str] = None
    publication_status: Optional[str] = None  # 'agree', 'disagree', 'pending', or None
    created_at: str
    updated_at: str


class StakeholderMention(BaseModel):
    id: str
    chunk_id: str
    stakeholder_id: str
    stakeholder: Stakeholder
    confidence: float
    mention_text: str
    mention_bbox: BoundingBox
    verified: Optional[bool] = None
    created_at: str


class StakeholderListResponse(BaseModel):
    stakeholders: List[Stakeholder]


class Chunk(BaseModel):
    id: str
    document_id: str
    page: int
    context: str
    bbox: BoundingBox


class ChunkDetail(BaseModel):
    id: str
    document_id: str
    page: int
    context: str
    bbox: BoundingBox
    stakeholder_mentions: List[StakeholderMention]


class ChunkListResponse(BaseModel):
    chunks: List[ChunkDetail]


class DocumentDetail(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    parse_status: Optional[str] = None
    uploaded_at: Optional[str] = None
    processed_at: Optional[str] = None
    created_at: str
    updated_at: str
    chunks: List[ChunkDetail]
    pdf_url: Optional[str] = None


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/transform", response_model=TextOutput)
def transform(input_data: TextInput):
    """Transform text by randomly changing words"""
    original_text = input_data.text
    transformed_text = transform_text(original_text)
    return TextOutput(original=original_text, transformed=transformed_text)


# Authentication routes
@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Login - finds user by username or email"""
    # Find user by username or email
    logger.info(f"Login request: {request}")
    user = db.get_user_by_username(request.username)
    logger.info(f"User: {user}")
    if not user:
        user = db.get_user_by_email(request.email)

    if not user:
        # Create a dummy user for any login attempt
        user = {
            "id": f"user_{len(db.get_users()) + 1}",
            "username": request.username,
            "email": request.email,
            "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={request.username}",
        }

    return LoginResponse(user=User(**user), token=f"token_{user['id']}_{datetime.now().isoformat()}")


@app.post("/auth/logout", response_model=LogoutResponse)
def logout():
    """Dummy logout - always succeeds"""
    logger.info("Logout request")
    return LogoutResponse(success=True, message="Logged out successfully")


@app.get("/auth/me", response_model=AuthMeResponse)
def get_current_user():
    """Get current user - returns the first user for now"""
    users = db.get_users()[0]
    logger.info(f"Users: {users[0]}")
    if not users:
        raise HTTPException(status_code=401, detail="No users found")
    return AuthMeResponse(user=User(**users[0]))


# Workspace routes
@app.get("/workspaces", response_model=WorkspaceListResponse)
def get_workspaces():
    """Get all workspaces"""
    workspaces_data = db.get_workspaces()
    workspaces = []
    logger.info(f"Workspaces: {workspaces_data}")
    for ws in workspaces_data:
        workspaces.append(
            Workspace(
                id=ws["id"],
                name=ws["name"],
                description=ws.get("description", ""),
                created_at=ws["created_at"],
                updated_at=ws["updated_at"],
                member_count=ws["member_count"],
                is_owner=bool(ws.get("is_owner", 0)),
            )
        )
    return WorkspaceListResponse(workspaces=workspaces)


@app.post("/workspaces", response_model=CreateWorkspaceResponse)
def create_workspace(request: CreateWorkspaceRequest):
    """Create a new workspace"""
    logger.info(f"Create workspace request: {request}")
    new_workspace = {
        "id": f"workspace_{len(db.get_workspaces()) + 1}",
        "name": request.name,
        "description": request.description or "New workspace",
        "created_at": datetime.now().isoformat() + "Z",
        "updated_at": datetime.now().isoformat() + "Z",
        "member_count": 1,
        "is_owner": True,
    }

    return CreateWorkspaceResponse(workspace=Workspace(**new_workspace))


@app.get("/workspaces/{workspace_id}", response_model=WorkspaceDetailResponse)
def get_workspace_detail(workspace_id: str):
    """Get detailed workspace information"""
    workspace = db.get_workspace_by_id(workspace_id)
    logger.info(f"Workspace: {workspace}")
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get workspace members
    members_data = db.get_workspace_members(workspace_id)
    members = [User(**member) for member in members_data]

    # Get all documents (for now, return all documents - in a real app, filter by workspace)
    documents_data = db.get_documents()
    documents = []
    for doc in documents_data:
        documents.append(
            Document(
                id=doc["id"],
                title=doc["title"],
                description=doc.get("description"),
                type=doc.get("type"),
                file_path=doc.get("file_path"),
                file_size=doc.get("file_size"),
                page_count=doc.get("page_count"),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
            )
        )

    # Create detailed workspace
    detailed_workspace = WorkspaceDetail(
        id=workspace["id"],
        name=workspace["name"],
        description=workspace.get("description", ""),
        created_at=workspace["created_at"],
        updated_at=workspace["updated_at"],
        member_count=workspace["member_count"],
        is_owner=bool(workspace.get("is_owner", 0)),
        members=members,
        documents=documents,
    )

    return WorkspaceDetailResponse(workspace=detailed_workspace)


# Cases routes
@app.get("/cases", response_model=CaseListResponse)
def get_cases():
    """Get all cases"""
    cases_data = db.get_cases()
    cases = []
    logger.info(f"Cases: {cases_data}")
    for case in cases_data:
        cases.append(
            Case(
                id=case["id"],
                title=case["title"],
                description=case.get("description", ""),
                document_ids=case["document_ids"],
                created_at=case["created_at"],
                updated_at=case["updated_at"],
            )
        )
    return CaseListResponse(cases=cases)


@app.get("/cases/{case_id}", response_model=CaseDetailResponse)
def get_case_detail(case_id: str):
    """Get detailed case information"""
    case = db.get_case_by_id(case_id)
    logger.info(f"Case: {case}")
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get documents for this case
    case_documents = []
    for doc_id in case["document_ids"]:
        doc = db.get_document_by_id(doc_id)
        if doc:
            case_documents.append(
                Document(
                    id=doc["id"],
                    title=doc["title"],
                    description=doc.get("description"),
                    type=doc.get("type"),
                    file_path=doc.get("file_path"),
                    file_size=doc.get("file_size"),
                    page_count=doc.get("page_count"),
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"],
                )
            )

    detailed_case = CaseDetail(
        id=case["id"],
        title=case["title"],
        description=case.get("description", ""),
        document_ids=case["document_ids"],
        created_at=case["created_at"],
        updated_at=case["updated_at"],
        documents=case_documents,
    )

    return CaseDetailResponse(case=detailed_case)


@app.post("/cases", response_model=CreateCaseResponse)
def create_case(request: CreateCaseRequest):
    """Create a new case"""
    logger.info(f"Create case request: {request}")
    new_case = {
        "id": f"case_{len(db.get_cases()) + 1}",
        "title": request.title,
        "description": request.description,
        "document_ids": [],
        "created_at": datetime.now().isoformat() + "Z",
        "updated_at": datetime.now().isoformat() + "Z",
        "password": None,
    }

    db.create_case(new_case)

    return CreateCaseResponse(case=Case(**new_case))


@app.get("/cases/{case_id}/stakeholders", response_model=StakeholderListResponse)
def get_case_stakeholders(case_id: str):
    """Get all unique stakeholders for a case"""
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    stakeholders_data = db.get_case_stakeholders(case_id)
    stakeholders = []

    for stakeholder in stakeholders_data:
        stakeholders.append(
            Stakeholder(
                id=stakeholder["id"],
                type=stakeholder.get("type", ""),
                name=stakeholder["name"],
                contact_info=stakeholder.get("contact_info", ""),
                created_at=stakeholder["created_at"],
                updated_at=stakeholder["updated_at"],
            )
        )

    return StakeholderListResponse(stakeholders=stakeholders)


# Case Overview Models
class ObjectedChunk(BaseModel):
    """Chunk that was objected to"""

    chunk_id: str
    document_id: str
    document_title: str
    page: int
    context: str
    stakeholder_id: str
    stakeholder_name: str


class DocumentStatus(BaseModel):
    """Status of a document in the case"""

    document_id: str
    document_title: str
    is_ok: bool  # True if all stakeholders agree or no objections
    objected_chunks: List[ObjectedChunk]


class StakeholderResponse(BaseModel):
    """Stakeholder response information"""

    stakeholder_id: str
    stakeholder_name: str
    publication_status: Optional[str]  # 'agree', 'disagree', 'pending', or None
    has_replied: bool


class CaseOverviewResponse(BaseModel):
    """Complete overview of case status"""

    case_id: str
    case_title: str
    documents: List[DocumentStatus]
    stakeholders: List[StakeholderResponse]
    total_documents: int
    total_objected_chunks: int
    all_stakeholders_responded: bool


@app.get("/cases/{case_id}/overview", response_model=CaseOverviewResponse)
def get_case_overview(case_id: str):
    """
    Get comprehensive overview of case including document status, objected chunks, and stakeholder responses.

    This endpoint provides:
    - Status of each document (ok vs has objections)
    - List of objected chunks with stakeholder information
    - Response status of each stakeholder
    - Overall case completion status
    """
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get all documents for this case
    document_ids = case.get("document_ids", [])
    documents_status = []
    total_objected_chunks = 0
    all_stakeholder_ids = set()

    # Get all stakeholders for this case (with publication_status)
    stakeholders_data = db.get_case_stakeholders(case_id)
    stakeholders_map = {}
    for s in stakeholders_data:
        # Get full stakeholder data including publication_status
        full_stakeholder = db.get_stakeholder_by_id(s["id"])
        if full_stakeholder:
            stakeholders_map[s["id"]] = full_stakeholder
        else:
            stakeholders_map[s["id"]] = s

    # Get all sent emails for this case to check responses
    sent_emails_data = db.get_sent_emails(case_id=case_id)
    stakeholder_email_map = {}  # stakeholder_id -> list of sent emails
    for email in sent_emails_data:
        stakeholder_id = email.get("stakeholder_id")
        if stakeholder_id:
            if stakeholder_id not in stakeholder_email_map:
                stakeholder_email_map[stakeholder_id] = []
            stakeholder_email_map[stakeholder_id].append(email)

    # Check which stakeholders have replied
    stakeholder_has_replied = {}
    for stakeholder_id, emails in stakeholder_email_map.items():
        has_reply = False
        for email in emails:
            replies = db.get_email_replies(email["id"])
            if replies:
                has_reply = True
                break
        stakeholder_has_replied[stakeholder_id] = has_reply

    # Process each document
    for doc_id in document_ids:
        doc = db.get_document_by_id(doc_id)
        if not doc:
            continue

        # Get all chunks for this document with case-specific verification status
        chunks = db.get_chunks_by_document(doc_id)
        objected_chunks = []

        for chunk in chunks:
            # Get stakeholder mentions for this chunk with case verification
            chunk_stakeholders = db.get_chunk_stakeholders(chunk["id"], case_id=case_id)

            for cs in chunk_stakeholders:
                stakeholder_id = cs["stakeholder_id"]
                all_stakeholder_ids.add(stakeholder_id)

                # Check if this mention is objected (verified=False in CaseChunkStakeholderVerification)
                verification_status = db.get_case_mention_verification(case_id, cs["id"])

                # If verification is False (0), it means objected
                if verification_status is False:
                    stakeholder = stakeholders_map.get(stakeholder_id, {})
                    objected_chunks.append(
                        ObjectedChunk(
                            chunk_id=chunk["id"],
                            document_id=doc_id,
                            document_title=doc["title"],
                            page=chunk["page"],
                            context=chunk["context"],
                            stakeholder_id=stakeholder_id,
                            stakeholder_name=stakeholder.get("name", "Unknown"),
                        )
                    )
                    total_objected_chunks += 1

        # Document is OK if no objected chunks
        documents_status.append(
            DocumentStatus(
                document_id=doc_id,
                document_title=doc["title"],
                is_ok=(len(objected_chunks) == 0),
                objected_chunks=objected_chunks,
            )
        )

    # Build stakeholder responses list
    stakeholder_responses = []
    for stakeholder_id, stakeholder_data in stakeholders_map.items():
        stakeholder_responses.append(
            StakeholderResponse(
                stakeholder_id=stakeholder_id,
                stakeholder_name=stakeholder_data.get("name", ""),
                publication_status=stakeholder_data.get("publication_status"),
                has_replied=stakeholder_has_replied.get(stakeholder_id, False),
            )
        )

    # Check if all stakeholders have responded
    all_responded = len(all_stakeholder_ids) > 0 and all(
        stakeholder_has_replied.get(sid, False) for sid in all_stakeholder_ids
    )

    return CaseOverviewResponse(
        case_id=case_id,
        case_title=case["title"],
        documents=documents_status,
        stakeholders=stakeholder_responses,
        total_documents=len(documents_status),
        total_objected_chunks=total_objected_chunks,
        all_stakeholders_responded=all_responded,
    )


# Documents routes
@app.get("/documents")
def get_documents():
    """Get all documents"""
    documents_data = db.get_documents()
    documents = []
    logger.info(f"Documents: {documents_data}")
    for doc in documents_data:
        documents.append(
            Document(
                id=doc["id"],
                title=doc["title"],
                description=doc.get("description"),
                type=doc.get("type"),
                file_path=doc.get("file_path"),
                file_size=doc.get("file_size"),
                page_count=doc.get("page_count"),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
            )
        )
    return {"documents": documents}


@app.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document_detail(document_id: str, case_id: Optional[str] = Query(None)):
    """Get detailed document information with chunks and stakeholder mentions, optionally filtered by case for verification status"""
    document = db.get_document_by_id(document_id)
    logger.info(f"Document: {document}")
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunks for this document
    document_chunks = db.get_chunks_by_document(document_id)

    chunks_with_mentions = []
    for chunk in document_chunks:
        # Get stakeholder mentions for this chunk
        chunk_stakeholders = db.get_chunk_stakeholders(chunk["id"], case_id=case_id)

        stakeholder_mentions = []
        for cs in chunk_stakeholders:
            stakeholder = db.get_stakeholder_by_id(cs["stakeholder_id"])
            if stakeholder:
                stakeholder_mentions.append(
                    StakeholderMention(
                        id=cs["id"],
                        chunk_id=cs["chunk_id"],
                        stakeholder_id=cs["stakeholder_id"],
                        stakeholder=Stakeholder(
                            id=stakeholder["id"],
                            type=stakeholder.get("type"),
                            name=stakeholder["name"],
                            contact_info=stakeholder.get("contact_info"),
                            publication_status=stakeholder.get("publication_status"),
                            created_at=stakeholder["created_at"],
                            updated_at=stakeholder["updated_at"],
                        ),
                        confidence=cs["confidence"],
                        mention_text=cs["mention_text"],
                        mention_bbox=BoundingBox(**cs["mention_bbox"]),
                        verified=bool(cs["verified"]) if cs["verified"] is not None else None,
                        created_at=cs["created_at"],
                    )
                )

        chunks_with_mentions.append(
            ChunkDetail(
                id=chunk["id"],
                document_id=chunk["document_id"],
                page=chunk["page"],
                context=chunk["context"],
                bbox=BoundingBox(**chunk["bbox"]),
                stakeholder_mentions=stakeholder_mentions,
            )
        )

    base_url = "http://localhost:8000"
    pdf_url = f"{base_url}/documents/{document_id}/pdf"

    return DocumentDetail(
        id=document["id"],
        title=document["title"],
        description=document.get("description"),
        type=document.get("type"),
        file_path=document.get("file_path"),
        file_size=document.get("file_size"),
        page_count=document.get("page_count"),
        parse_status=document.get("parse_status"),
        uploaded_at=document.get("uploaded_at"),
        processed_at=document.get("processed_at"),
        created_at=document["created_at"],
        updated_at=document["updated_at"],
        chunks=chunks_with_mentions,
        pdf_url=pdf_url,
    )


@app.get("/documents/{document_id}/pdf")
def get_document_pdf(document_id: str):
    """Serve the PDF file for a document"""
    document = db.get_document_by_id(document_id)
    logger.info(f"Document: {document}")
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.get("file_path"):
        raise HTTPException(status_code=404, detail="Document has no file path")

    file_path = Path(__file__).parent / document["file_path"]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document["title"] + ".pdf",
    )


@app.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
def get_document_chunks(document_id: str, case_id: Optional[str] = Query(None)):
    """Get all chunks for a document with stakeholder mentions, optionally filtered by case for verification status"""
    document = db.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document_chunks = db.get_chunks_by_document(document_id)
    logger.info(f"Document chunks: {document_chunks}")
    if not document_chunks:
        return ChunkListResponse(chunks=[])

    chunks_with_mentions = []
    for chunk in document_chunks:
        chunk_stakeholders = db.get_chunk_stakeholders(chunk["id"], case_id=case_id)

        stakeholder_mentions = []
        for cs in chunk_stakeholders:
            stakeholder = db.get_stakeholder_by_id(cs["stakeholder_id"])
            if stakeholder:
                stakeholder_mentions.append(
                    StakeholderMention(
                        id=cs["id"],
                        chunk_id=cs["chunk_id"],
                        stakeholder_id=cs["stakeholder_id"],
                        stakeholder=Stakeholder(
                            id=stakeholder["id"],
                            type=stakeholder.get("type"),
                            name=stakeholder["name"],
                            contact_info=stakeholder.get("contact_info"),
                            publication_status=stakeholder.get("publication_status"),
                            created_at=stakeholder["created_at"],
                            updated_at=stakeholder["updated_at"],
                        ),
                        confidence=cs["confidence"],
                        mention_text=cs["mention_text"],
                        mention_bbox=BoundingBox(**cs["mention_bbox"]),
                        verified=bool(cs["verified"]) if cs["verified"] is not None else None,
                        created_at=cs["created_at"],
                    )
                )

        chunks_with_mentions.append(
            ChunkDetail(
                id=chunk["id"],
                document_id=chunk["document_id"],
                page=chunk["page"],
                context=chunk["context"],
                bbox=BoundingBox(**chunk["bbox"]),
                stakeholder_mentions=stakeholder_mentions,
            )
        )

    return ChunkListResponse(chunks=chunks_with_mentions)


class UploadDocumentResponse(BaseModel):
    document: Document


def background_parse_document(doc_id: str, page_count: int):
    """Background task to parse document and generate fake chunks/stakeholders"""
    logger.info(f"Starting background parsing for document {doc_id}")
    parse_pdf(doc_id)
    logger.info("Starting entity extraction")
    document = db.get_document_by_id(doc_id)
    processor = MarkdownNERProcessor(
        markdown_path=str(document["markdown_path"]),
        pdf_path=str(document["file_path"]),  # ← PDF for chunking and bounding boxes
        document_id=doc_id,
        entity_types=None,
        stakeholder_types_to_save=["person", "organization"],
        min_confidence=0.0,
        model_type="xlm-roberta",
        model_name="Davlan/xlm-roberta-base-ner-hrl",
        verbose=True,
    )
    results = processor.process(create_chunks=True)

    document["parse_status"] = "completed"
    db.update_document(doc_id, document)

    #     logger.info(f"Starting background parsing for document {doc_id}")
    #     parse_pdf(doc_id)
    #     logger.info(f"Document {doc_id} parsed successfully")

    #     chunks = generate_fake_chunks(doc_id, page_count)
    #     new_stakeholders = generate_fake_stakeholders(num_stakeholders=5)
    #     # Save chunks to database
    #     for chunk in chunks:
    #         db.create_chunk(chunk)

    #     # Save stakeholders to database (avoid duplicates by name)
    #     existing_stakeholders_dict = {s["name"]: s for s in db.get_stakeholders()}
    #     stakeholders_to_use = []

    #     for stakeholder in new_stakeholders:
    #         if stakeholder["name"] not in existing_stakeholders_dict:
    #             db.create_stakeholder(stakeholder)
    #             stakeholders_to_use.append(stakeholder)
    #         else:
    #             stakeholders_to_use.append(existing_stakeholders_dict[stakeholder["name"]])

    #     # Generate and save chunk-stakeholder relationships
    #     chunk_stakeholders = generate_fake_chunk_stakeholders(chunks, stakeholders_to_use)
    #     for cs in chunk_stakeholders:
    #         db.create_chunk_stakeholder(cs)

    #     logger.info(
    #         f"Generated {len(chunks)} chunks and {len(chunk_stakeholders)} stakeholder mentions for document {doc_id}"
    #     )

    # except Exception as e:
    #     logger.error(f"Error processing document {doc_id} in background: {e}", exc_info=True)


@app.post("/documents/upload", response_model=UploadDocumentResponse)
async def upload_document(
    case_id: str, file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload a PDF document to a case"""
    logger.info(f"Upload document request: {case_id}, {file.filename}")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Find the case
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Generate unique document ID
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    # Save file
    file_path = data_dir / f"{doc_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = file_path.stat().st_size

    # Dummy page count (assume 3-5 pages for now)
    page_count = random.randint(3, 5)

    # Create document record
    now = datetime.now().isoformat() + "Z"
    new_document = {
        "id": doc_id,
        "title": file.filename,
        "description": "",
        "type": "pdf",
        "keywords": None,
        "author": None,
        "file_path": str(file_path.relative_to(Path(__file__).parent)),
        "markdown_path": None,
        "file_size": file_size,
        "page_count": 0,  # Would need PDF parsing to get actual page count
        "parse_status": "pending",
        "created_at": now,
        "updated_at": now,
    }

    db.create_document(new_document)
    db.add_document_to_case(case_id, doc_id)

    # Run parsing and chunk generation in the background
    background_tasks.add_task(background_parse_document, doc_id, page_count)

    return_document = Document(
        id=new_document["id"],
        title=new_document["title"],
        description=new_document["description"],
        type=new_document["type"],
        file_path=new_document["file_path"],
        file_size=new_document["file_size"],
        page_count=new_document["page_count"],
        parse_status=new_document["parse_status"],
        created_at=new_document["created_at"],
        updated_at=new_document["updated_at"],
    )

    return UploadDocumentResponse(document=return_document)


# Stakeholder routes
class CreateStakeholderRequest(BaseModel):
    type: Optional[str] = None
    name: str
    contact_info: Optional[str] = None
    publication_status: Optional[str] = None  # 'agree', 'disagree', 'pending', or None


class UpdateStakeholderPublicationStatusRequest(BaseModel):
    publication_status: Optional[str] = None  # 'agree', 'disagree', 'pending', or None


class StakeholderResponse(BaseModel):
    stakeholder: Stakeholder


class StakeholderListResponse(BaseModel):
    stakeholders: List[Stakeholder]


class CreateStakeholderResponse(BaseModel):
    stakeholder: Stakeholder


@app.post("/stakeholders", response_model=CreateStakeholderResponse)
def create_stakeholder(request: CreateStakeholderRequest):
    """Create a new stakeholder"""
    # Validate publication_status if provided
    if request.publication_status:
        valid_statuses = ["agree", "disagree", "pending"]
        if request.publication_status not in valid_statuses:
            raise HTTPException(
                status_code=400, detail=f"Invalid publication_status. Must be one of: {', '.join(valid_statuses)}"
            )

    # Generate ID and timestamps
    stakeholder_id = f"stakeholder_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat() + "Z"

    # Create stakeholder data
    new_stakeholder = {
        "id": stakeholder_id,
        "type": request.type,
        "name": request.name,
        "contact_info": request.contact_info,
        "publication_status": request.publication_status,
        "created_at": now,
        "updated_at": now,
    }

    # Save to database
    db.create_stakeholder(new_stakeholder)

    # Return created stakeholder
    return CreateStakeholderResponse(
        stakeholder=Stakeholder(
            id=new_stakeholder["id"],
            type=new_stakeholder.get("type"),
            name=new_stakeholder["name"],
            contact_info=new_stakeholder.get("contact_info"),
            publication_status=new_stakeholder.get("publication_status"),
            created_at=new_stakeholder["created_at"],
            updated_at=new_stakeholder["updated_at"],
        )
    )


@app.get("/stakeholders", response_model=StakeholderListResponse)
def get_stakeholders():
    """Get all stakeholders"""
    stakeholders_data = db.get_stakeholders()
    stakeholders = []
    for stakeholder in stakeholders_data:
        stakeholders.append(
            Stakeholder(
                id=stakeholder["id"],
                type=stakeholder.get("type"),
                name=stakeholder["name"],
                contact_info=stakeholder.get("contact_info"),
                publication_status=stakeholder.get("publication_status"),
                created_at=stakeholder["created_at"],
                updated_at=stakeholder["updated_at"],
            )
        )
    return StakeholderListResponse(stakeholders=stakeholders)


@app.get("/stakeholders/{stakeholder_id}", response_model=StakeholderResponse)
def get_stakeholder(stakeholder_id: str):
    """Get a stakeholder by ID"""
    stakeholder = db.get_stakeholder_by_id(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    return StakeholderResponse(
        stakeholder=Stakeholder(
            id=stakeholder["id"],
            type=stakeholder.get("type"),
            name=stakeholder["name"],
            contact_info=stakeholder.get("contact_info"),
            publication_status=stakeholder.get("publication_status", "pending"),
            created_at=stakeholder["created_at"],
            updated_at=stakeholder["updated_at"],
        )
    )


@app.patch("/stakeholders/{stakeholder_id}/publication-status", response_model=StakeholderResponse)
def update_stakeholder_publication_status(stakeholder_id: str, request: UpdateStakeholderPublicationStatusRequest):
    """Update a stakeholder's publication status"""
    # Validate publication_status value if provided
    if request.publication_status is not None:
        valid_statuses = ["agree", "disagree", "pending"]
        if request.publication_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid publication_status. Must be one of: {', '.join(valid_statuses)}, or null",
            )

    # Check if stakeholder exists
    stakeholder = db.get_stakeholder_by_id(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Update the stakeholder
    db.update_stakeholder(stakeholder_id, {"publication_status": request.publication_status})

    # Return updated stakeholder
    updated_stakeholder = db.get_stakeholder_by_id(stakeholder_id)
    return StakeholderResponse(
        stakeholder=Stakeholder(
            id=updated_stakeholder["id"],
            type=updated_stakeholder.get("type"),
            name=updated_stakeholder["name"],
            contact_info=updated_stakeholder.get("contact_info"),
            publication_status=updated_stakeholder.get("publication_status"),
            created_at=updated_stakeholder["created_at"],
            updated_at=updated_stakeholder["updated_at"],
        )
    )


# =============================================================================
# EMAIL INTEGRATION
# =============================================================================
# Microsoft Outlook email integration via Microsoft Graph API
# Provides OAuth authentication and email operations
#
# Available endpoints:
#   - GET  /email/authorize           - Get OAuth URL
#   - GET  /email/callback            - OAuth callback (automatic)
#   - GET  /email/status              - Check token status
#   - POST /email/send                - Send an email
#   - GET  /email/messages            - List emails
#   - GET  /email/messages/{id}       - Get email details
#   - POST /email/messages/{id}/read  - Mark as read/unread
#   - DELETE /email/revoke            - Revoke access
#
# Configuration:
#   Required environment variables:
#   - MICROSOFT_CLIENT_ID
#   - MICROSOFT_CLIENT_SECRET
#   - MICROSOFT_REDIRECT_URI
#
# See backend/server/email/README.md for detailed documentation
# =============================================================================

# =============================================================================


from server.email import email_router
from server.reply_classification import classification_router

app.include_router(email_router)

# =============================================================================
# REPLY CLASSIFICATION
# =============================================================================
# Sentiment classification for stakeholder responses using zero-shot NLP
# Determines whether responses agree to or object to publication
#
# Available endpoints:
#   - POST /classification/classify  - Classify text sentiment
#   - GET  /classification/health    - Check service status
#
# Model:
#   - cross-encoder/nli-deberta-v3-small (zero-shot classification)
#   - Candidate labels: "agrees to publish", "objects to publication"
#
# See backend/server/reply_classification/README.md for detailed documentation
# =============================================================================

app.include_router(classification_router)


# VERIFICATION INTEGRATION
# =============================================================================
# Verification endpoints for chunk stakeholder mentions
# Provides functionality to verify or unverify stakeholder mentions individually
# or in bulk based on confidence thresholds
#
# Available endpoints:
#   - POST /verification/mention/{mention_id}  - Verify/unverify single mention
#   - POST /verification/bulk                  - Bulk verify mentions by filter
#
# Bulk verification filters:
#   - "high"   - Verify mentions with confidence >= 0.9
#   - "medium" - Verify mentions with confidence >= 0.7
#   - "all"    - Verify all unverified mentions regardless of confidence
#
# See backend/server/verification.py for implementation details
# =============================================================================

from server.verification import verification_router

app.include_router(verification_router)


# =============================================================================
# PDF GENERATION INTEGRATION
# =============================================================================
# PDF generation endpoints for stakeholders
# Provides functionality to generate PDFs based on stakeholder mentions
#
# Available endpoints:
#   - POST /pdf/stakeholders/{stakeholder_id}/generate  - Generate PDF for stakeholder
#
# Content types:
#   - "full_documents" - Include all PDF documents from the case
#   - "pages_only"     - Extract only pages containing stakeholder mentions
#   - "chunks_only"    - Create text-based PDF with chunk excerpts
#
# See backend/server/pdf.py for implementation details
# =============================================================================

from server.pdf import pdf_router

app.include_router(pdf_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
