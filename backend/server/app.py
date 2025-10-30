from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from .utils.text_processor import transform_text

app = FastAPI(title="WOO Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dummy data for development
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
    },
    {
        "id": "workspace_2",
        "name": "Design Team",
        "description": "UI/UX design collaboration space",
        "createdAt": "2024-01-10T09:00:00Z",
        "updatedAt": "2024-01-18T11:45:00Z",
        "memberCount": 5,
        "isOwner": False,
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
    """Dummy login - accepts any username/email combination"""
    # Find user by username/email or create a dummy one
    user = None
    for u in DUMMY_USERS:
        if u["username"] == request.username or u["email"] == request.email:
            user = u
            break

    if not user:
        # Create a dummy user for any login attempt
        user = {
            "id": f"user_{len(DUMMY_USERS) + 1}",
            "username": request.username,
            "email": request.email,
            "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={request.username}",
        }

    return LoginResponse(user=User(**user), token=f"dummy_token_{user['id']}_{datetime.now().isoformat()}")


@app.post("/auth/logout", response_model=LogoutResponse)
def logout():
    """Dummy logout - always succeeds"""
    return LogoutResponse(success=True, message="Logged out successfully")


@app.get("/auth/me", response_model=AuthMeResponse)
def get_current_user():
    """Dummy current user - returns the first user"""
    return AuthMeResponse(user=User(**DUMMY_USERS[0]))


# Workspace routes
@app.get("/workspaces", response_model=WorkspaceListResponse)
def get_workspaces():
    """Get all workspaces"""
    return WorkspaceListResponse(workspaces=[Workspace(**ws) for ws in DUMMY_WORKSPACES])


@app.post("/workspaces", response_model=CreateWorkspaceResponse)
def create_workspace(request: CreateWorkspaceRequest):
    """Create a new workspace"""
    new_workspace = {
        "id": f"workspace_{len(DUMMY_WORKSPACES) + 1}",
        "name": request.name,
        "description": request.description or "New workspace",
        "createdAt": datetime.now().isoformat() + "Z",
        "updatedAt": datetime.now().isoformat() + "Z",
        "memberCount": 1,
        "isOwner": True,
    }

    # In a real implementation, this would be saved to database
    # DUMMY_WORKSPACES.append(new_workspace)

    return CreateWorkspaceResponse(workspace=Workspace(**new_workspace))


@app.get("/workspaces/{workspace_id}", response_model=WorkspaceDetailResponse)
def get_workspace_detail(workspace_id: str):
    """Get detailed workspace information"""
    workspace = None
    for ws in DUMMY_WORKSPACES:
        if ws["id"] == workspace_id:
            workspace = ws
            break

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Create detailed workspace with members and documents
    detailed_workspace = WorkspaceDetail(
        **workspace,
        members=[User(**u) for u in DUMMY_USERS[: workspace["memberCount"]]],
        documents=[Document(**doc) for doc in DUMMY_DOCUMENTS],
    )

    return WorkspaceDetailResponse(workspace=detailed_workspace)


# Cases routes
@app.get("/cases", response_model=CaseListResponse)
def get_cases():
    """Get all cases"""
    return CaseListResponse(cases=[Case(**case) for case in DUMMY_CASES])


@app.get("/cases/{case_id}", response_model=CaseDetailResponse)
def get_case_detail(case_id: str):
    """Get detailed case information"""
    case = None
    for c in DUMMY_CASES:
        if c["id"] == case_id:
            case = c
            break

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case_documents = [Document(**doc) for doc in DUMMY_DOCUMENTS if doc["id"] in case["documentIds"]]

    detailed_case = CaseDetail(
        **case,
        documents=case_documents,
    )

    return CaseDetailResponse(case=detailed_case)


@app.post("/cases", response_model=CreateCaseResponse)
def create_case(request: CreateCaseRequest):
    """Create a new case"""
    new_case = {
        "id": f"case_{len(DUMMY_CASES) + 1}",
        "title": request.title,
        "description": request.description,
        "documentIds": [],
        "createdAt": datetime.now().isoformat() + "Z",
        "updatedAt": datetime.now().isoformat() + "Z",
    }

    return CreateCaseResponse(case=Case(**new_case))


# Documents routes
@app.get("/documents")
def get_documents():
    """Get all documents"""
    return {"documents": [Document(**doc) for doc in DUMMY_DOCUMENTS]}


@app.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document_detail(document_id: str):
    """Get detailed document information with chunks and stakeholder mentions"""
    document = None
    for doc in DUMMY_DOCUMENTS:
        if doc["id"] == document_id:
            document = doc
            break

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document_chunks = [chunk for chunk in DUMMY_CHUNKS if chunk["documentId"] == document_id]

    chunks_with_mentions = []
    for chunk in document_chunks:
        chunk_stakeholders = [cs for cs in DUMMY_CHUNK_STAKEHOLDERS if cs["chunkId"] == chunk["id"]]

        stakeholder_mentions = []
        for cs in chunk_stakeholders:
            stakeholder = next((s for s in DUMMY_STAKEHOLDERS if s["id"] == cs["stakeholderId"]), None)
            if stakeholder:
                stakeholder_mentions.append(
                    StakeholderMention(
                        id=cs["id"],
                        chunkId=cs["chunkId"],
                        stakeholderId=cs["stakeholderId"],
                        stakeholder=Stakeholder(**stakeholder),
                        confidence=cs["confidence"],
                        mentionText=cs["mentionText"],
                        mentionBbox=BoundingBox(**cs["mentionBbox"]),
                        verified=cs["verified"],
                        createdAt=cs["createdAt"],
                    )
                )

        chunks_with_mentions.append(
            ChunkDetail(
                id=chunk["id"],
                documentId=chunk["documentId"],
                page=chunk["page"],
                context=chunk["context"],
                bbox=BoundingBox(**chunk["bbox"]),
                stakeholderMentions=stakeholder_mentions,
            )
        )

    base_url = "http://localhost:8000"
    pdf_url = f"{base_url}/documents/{document_id}/pdf"

    return DocumentDetail(
        **document,
        chunks=chunks_with_mentions,
        pdfUrl=pdf_url,
    )


@app.get("/documents/{document_id}/pdf")
def get_document_pdf(document_id: str):
    """Serve the PDF file for a document"""
    document = None
    for doc in DUMMY_DOCUMENTS:
        if doc["id"] == document_id:
            document = doc
            break

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(__file__).parent / document["filePath"]

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
    document_chunks = [chunk for chunk in DUMMY_CHUNKS if chunk["documentId"] == document_id]

    if not document_chunks:
        raise HTTPException(status_code=404, detail="Document or chunks not found")

    chunks_with_mentions = []
    for chunk in document_chunks:
        chunk_stakeholders = [cs for cs in DUMMY_CHUNK_STAKEHOLDERS if cs["chunkId"] == chunk["id"]]

        stakeholder_mentions = []
        for cs in chunk_stakeholders:
            stakeholder = next((s for s in DUMMY_STAKEHOLDERS if s["id"] == cs["stakeholderId"]), None)
            if stakeholder:
                stakeholder_mentions.append(
                    StakeholderMention(
                        id=cs["id"],
                        chunkId=cs["chunkId"],
                        stakeholderId=cs["stakeholderId"],
                        stakeholder=Stakeholder(**stakeholder),
                        confidence=cs["confidence"],
                        mentionText=cs["mentionText"],
                        mentionBbox=BoundingBox(**cs["mentionBbox"]),
                        verified=cs["verified"],
                        createdAt=cs["createdAt"],
                    )
                )

        chunks_with_mentions.append(
            ChunkDetail(
                id=chunk["id"],
                documentId=chunk["documentId"],
                page=chunk["page"],
                context=chunk["context"],
                bbox=BoundingBox(**chunk["bbox"]),
                stakeholderMentions=stakeholder_mentions,
            )
        )

    return ChunkListResponse(chunks=chunks_with_mentions)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
