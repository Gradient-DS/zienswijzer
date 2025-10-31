from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
#from .utils.text_processor import transform_text
from . import db
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import shutil
import uuid
from .utils.text_processor import transform_text
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
    createdAt: str
    updatedAt: str
    memberCount: int
    isOwner: bool


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Document(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: Optional[str] = None
    filePath: Optional[str] = None
    fileSize: Optional[int] = None
    pageCount: Optional[int] = None
    processingStatus: Optional[str] = None
    uploadedAt: Optional[str] = None
    processedAt: Optional[str] = None
    createdAt: str
    updatedAt: str
    content: Optional[str] = None
    authorId: Optional[str] = None


class WorkspaceDetail(BaseModel):
    id: str
    name: str
    description: str
    createdAt: str
    updatedAt: str
    memberCount: int
    isOwner: bool
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
    documentIds: List[str]
    createdAt: str
    updatedAt: str


class CaseDetail(BaseModel):
    id: str
    title: str
    description: str
    documentIds: List[str]
    createdAt: str
    updatedAt: str
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
    type: str
    name: str
    contactInfo: str
    createdAt: str
    updatedAt: str


class StakeholderMention(BaseModel):
    id: str
    chunkId: str
    stakeholderId: str
    stakeholder: Stakeholder
    confidence: float
    mentionText: str
    mentionBbox: BoundingBox
    verified: bool
    createdAt: str


class Chunk(BaseModel):
    id: str
    documentId: str
    page: int
    context: str
    bbox: BoundingBox


class ChunkDetail(BaseModel):
    id: str
    documentId: str
    page: int
    context: str
    bbox: BoundingBox
    stakeholderMentions: List[StakeholderMention]


class ChunkListResponse(BaseModel):
    chunks: List[ChunkDetail]


class DocumentDetail(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: Optional[str] = None
    filePath: Optional[str] = None
    fileSize: Optional[int] = None
    pageCount: Optional[int] = None
    processingStatus: Optional[str] = None
    uploadedAt: Optional[str] = None
    processedAt: Optional[str] = None
    createdAt: str
    updatedAt: str
    chunks: List[ChunkDetail]
    pdfUrl: Optional[str] = None


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
        workspaces.append(Workspace(
            id=ws["id"],
            name=ws["name"],
            description=ws.get("description", ""),
            createdAt=ws["created_at"],
            updatedAt=ws["updated_at"],
            memberCount=ws["member_count"],
            isOwner=bool(ws.get("is_owner", 0))
        ))
    return WorkspaceListResponse(workspaces=workspaces)


@app.post("/workspaces", response_model=CreateWorkspaceResponse)
def create_workspace(request: CreateWorkspaceRequest):
    """Create a new workspace"""
    logger.info(f"Create workspace request: {request}")
    new_workspace = {
        "id": f"workspace_{len(db.get_workspaces()) + 1}",
        "name": request.name,
        "description": request.description or "New workspace",
        "createdAt": datetime.now().isoformat() + "Z",
        "updatedAt": datetime.now().isoformat() + "Z",
        "memberCount": 1,
        "isOwner": True,
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
        documents.append(Document(
            id=doc["id"],
            title=doc["title"],
            description=doc.get("description"),
            type=doc.get("type"),
            filePath=doc.get("file_path"),
            fileSize=doc.get("file_size"),
            pageCount=doc.get("page_count"),
            processingStatus=doc.get("processing_status"),
            uploadedAt=doc.get("uploaded_at"),
            processedAt=doc.get("processed_at"),
            createdAt=doc["created_at"],
            updatedAt=doc["updated_at"]
        ))

    # Create detailed workspace
    detailed_workspace = WorkspaceDetail(
        id=workspace["id"],
        name=workspace["name"],
        description=workspace.get("description", ""),
        createdAt=workspace["created_at"],
        updatedAt=workspace["updated_at"],
        memberCount=workspace["member_count"],
        isOwner=bool(workspace.get("is_owner", 0)),
        members=members,
        documents=documents
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
        cases.append(Case(
            id=case["id"],
            title=case["title"],
            description=case.get("description", ""),
            documentIds=case["documentIds"],
            createdAt=case["created_at"],
            updatedAt=case["updated_at"]
        ))
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
    for doc_id in case["documentIds"]:
        doc = db.get_document_by_id(doc_id)
        if doc:
            case_documents.append(Document(
                id=doc["id"],
                title=doc["title"],
                description=doc.get("description"),
                type=doc.get("type"),
                filePath=doc.get("file_path"),
                fileSize=doc.get("file_size"),
                pageCount=doc.get("page_count"),
                processingStatus=doc.get("processing_status"),
                uploadedAt=doc.get("uploaded_at"),
                processedAt=doc.get("processed_at"),
                createdAt=doc["created_at"],
                updatedAt=doc["updated_at"]
            ))

    detailed_case = CaseDetail(
        id=case["id"],
        title=case["title"],
        description=case.get("description", ""),
        documentIds=case["documentIds"],
        createdAt=case["created_at"],
        updatedAt=case["updated_at"],
        documents=case_documents
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
        "documentIds": [],
        "createdAt": datetime.now().isoformat() + "Z",
        "updatedAt": datetime.now().isoformat() + "Z",
        "password": None,
    }

    db.create_case(new_case)

    return CreateCaseResponse(case=Case(**new_case))


# Documents routes
@app.get("/documents")
def get_documents():
    """Get all documents"""
    documents_data = db.get_documents()
    documents = []
    logger.info(f"Documents: {documents_data}")
    for doc in documents_data:
        documents.append(Document(
            id=doc["id"],
            title=doc["title"],
            description=doc.get("description"),
            type=doc.get("type"),
            filePath=doc.get("file_path"),
            fileSize=doc.get("file_size"),
            pageCount=doc.get("page_count"),
            processingStatus=doc.get("processing_status"),
            uploadedAt=doc.get("uploaded_at"),
            processedAt=doc.get("processed_at"),
            createdAt=doc["created_at"],
            updatedAt=doc["updated_at"]
        ))
    return {"documents": documents}


@app.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document_detail(document_id: str):
    """Get detailed document information with chunks and stakeholder mentions"""
    document = db.get_document_by_id(document_id)
    logger.info(f"Document: {document}")
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunks for this document
    document_chunks = db.get_chunks_by_document(document_id)

    chunks_with_mentions = []
    for chunk in document_chunks:
        # Get stakeholder mentions for this chunk
        chunk_stakeholders = db.get_chunk_stakeholders(chunk["id"])

        stakeholder_mentions = []
        for cs in chunk_stakeholders:
            stakeholder = db.get_stakeholder_by_id(cs["stakeholder_id"])
            if stakeholder:
                stakeholder_mentions.append(
                    StakeholderMention(
                        id=cs["id"],
                        chunkId=cs["chunk_id"],
                        stakeholderId=cs["stakeholder_id"],
                        stakeholder=Stakeholder(
                            id=stakeholder["id"],
                            type=stakeholder.get("type", ""),
                            name=stakeholder["name"],
                            contactInfo=stakeholder.get("contact_info", ""),
                            createdAt=stakeholder["created_at"],
                            updatedAt=stakeholder["updated_at"]
                        ),
                        confidence=cs["confidence"],
                        mentionText=cs["mention_text"],
                        mentionBbox=BoundingBox(**cs["mention_bbox"]),
                        verified=bool(cs["verified"]),
                        createdAt=cs["created_at"],
                    )
                )

        chunks_with_mentions.append(
            ChunkDetail(
                id=chunk["id"],
                documentId=chunk["document_id"],
                page=chunk["page"],
                context=chunk["context"],
                bbox=BoundingBox(**chunk["bbox"]),
                stakeholderMentions=stakeholder_mentions,
            )
        )

    base_url = "http://localhost:8000"
    pdf_url = f"{base_url}/documents/{document_id}/pdf"

    return DocumentDetail(
        id=document["id"],
        title=document["title"],
        description=document.get("description"),
        type=document.get("type"),
        filePath=document.get("file_path"),
        fileSize=document.get("file_size"),
        pageCount=document.get("page_count"),
        processingStatus=document.get("processing_status"),
        uploadedAt=document.get("uploaded_at"),
        processedAt=document.get("processed_at"),
        createdAt=document["created_at"],
        updatedAt=document["updated_at"],
        chunks=chunks_with_mentions,
        pdfUrl=pdf_url,
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
def get_document_chunks(document_id: str):
    """Get all chunks for a document with stakeholder mentions"""
    document_chunks = db.get_chunks_by_document(document_id)
    logger.info(f"Document chunks: {document_chunks}")
    if not document_chunks:
        raise HTTPException(status_code=404, detail="Document or chunks not found")

    chunks_with_mentions = []
    for chunk in document_chunks:
        chunk_stakeholders = db.get_chunk_stakeholders(chunk["id"])

        stakeholder_mentions = []
        for cs in chunk_stakeholders:
            stakeholder = db.get_stakeholder_by_id(cs["stakeholder_id"])
            if stakeholder:
                stakeholder_mentions.append(
                    StakeholderMention(
                        id=cs["id"],
                        chunkId=cs["chunk_id"],
                        stakeholderId=cs["stakeholder_id"],
                        stakeholder=Stakeholder(
                            id=stakeholder["id"],
                            type=stakeholder.get("type", ""),
                            name=stakeholder["name"],
                            contactInfo=stakeholder.get("contact_info", ""),
                            createdAt=stakeholder["created_at"],
                            updatedAt=stakeholder["updated_at"]
                        ),
                        confidence=cs["confidence"],
                        mentionText=cs["mention_text"],
                        mentionBbox=BoundingBox(**cs["mention_bbox"]),
                        verified=bool(cs["verified"]),
                        createdAt=cs["created_at"],
                    )
                )

        chunks_with_mentions.append(
            ChunkDetail(
                id=chunk["id"],
                documentId=chunk["document_id"],
                page=chunk["page"],
                context=chunk["context"],
                bbox=BoundingBox(**chunk["bbox"]),
                stakeholderMentions=stakeholder_mentions,
            )
        )

    return ChunkListResponse(chunks=chunks_with_mentions)


class UploadDocumentResponse(BaseModel):
    document: Document


@app.post("/documents/upload", response_model=UploadDocumentResponse)
async def upload_document(case_id: str, file: UploadFile = File(...)):
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

    # Create document record
    now = datetime.now().isoformat() + "Z"
    new_document = {
        "id": doc_id,
        "title": file.filename,
        "description": f"Uploaded document: {file.filename}",
        "type": "document",
        "filePath": str(file_path.relative_to(Path(__file__).parent)),
        "fileSize": file_size,
        "pageCount": 1,  # Would need PDF parsing to get actual page count
        "processingStatus": "completed",
        "uploadedAt": now,
        "processedAt": now,
        "createdAt": now,
        "updatedAt": now,
    }

    db.create_document(new_document)
    db.add_document_to_case(case_id, doc_id)
    
    return UploadDocumentResponse(document=Document(**new_document))


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

from server.email import email_router

app.include_router(email_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
