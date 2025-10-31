"""
Email integration with Microsoft Outlook using Graph API.

This module provides OAuth authentication and email operations (send, read)
for Microsoft Outlook accounts using the Microsoft Graph API.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import msal
import requests
import logging
import base64
import uuid
from pathlib import Path

from .config import email_config
from ..db.database import (
    get_oauth_token,
    save_oauth_token,
    delete_oauth_token,
    save_sent_email,
    get_sent_emails,
    get_sent_email_by_id,
    get_sent_email_by_conversation_id,
    save_email_reply,
    get_email_replies,
    get_email_reply_by_outlook_id,
    get_case_by_id,
    get_chunks_by_document,
    get_chunk_stakeholders,
    get_document_by_id,
)

logger = logging.getLogger(__name__)

# Router for email endpoints
email_router = APIRouter(prefix="/email", tags=["email"])


# Pydantic Models
class EmailAttachment(BaseModel):
    """Email attachment model"""

    name: str
    contentType: str
    contentBytes: Optional[str] = None  # Base64 encoded
    filePath: Optional[str] = None  # Path to file on disk (alternative to contentBytes)
    size: Optional[int] = None


class EmailAddress(BaseModel):
    """Email address with name"""

    address: EmailStr
    name: Optional[str] = None


class EmailMessage(BaseModel):
    """Email message model for reading emails"""

    id: str
    subject: str
    bodyPreview: str
    body: Optional[str] = None
    from_address: EmailAddress
    toRecipients: List[EmailAddress]
    ccRecipients: Optional[List[EmailAddress]] = None
    receivedDateTime: str
    isRead: bool
    hasAttachments: bool
    importance: str


class SendEmailRequest(BaseModel):
    """Request model for sending an email"""

    to: List[EmailAddress]
    subject: str
    body: str
    cc: Optional[List[EmailAddress]] = None
    bcc: Optional[List[EmailAddress]] = None
    bodyType: Optional[str] = "HTML"  # "HTML" or "Text"
    importance: Optional[str] = "normal"  # "low", "normal", "high"
    attachments: Optional[List[EmailAttachment]] = None


class TextChunk(BaseModel):
    """Text chunk from a document"""

    id: str
    text: str
    pageNumber: Optional[int] = None
    documentId: Optional[str] = None


class SendWOOEmailRequest(BaseModel):
    """Request model for sending a WOO (verzoek om inzage) email with template"""

    to: List[EmailAddress]
    subject: str
    requestDescription: str  # Description of the WOO request
    recipientName: str  # Name to use in greeting
    senderName: str  # Signature name
    chunks: List[TextChunk]  # Text chunks to include in email
    cc: Optional[List[EmailAddress]] = None
    bcc: Optional[List[EmailAddress]] = None
    bodyType: Optional[str] = "HTML"  # "HTML" or "Text"
    importance: Optional[str] = "normal"  # "low", "normal", "high"
    attachments: Optional[List[EmailAttachment]] = None


class SendStakeholderEmailRequest(BaseModel):
    """Request model for sending an email to a stakeholder based on their mentions"""

    stakeholder_id: str
    case_id: str
    user_id: str
    to: List[EmailAddress]
    subject: str
    content_type: str  # "full_documents", "pages_only", or "chunks_only"
    custom_message: Optional[str] = None
    cc: Optional[List[EmailAddress]] = None
    bcc: Optional[List[EmailAddress]] = None


class SendEmailResponse(BaseModel):
    """Response model after sending an email"""

    success: bool
    message: str
    messageId: Optional[str] = None


class EmailListResponse(BaseModel):
    """Response model for list of emails"""

    emails: List[EmailMessage]
    nextLink: Optional[str] = None
    total: int


class OAuthUrlResponse(BaseModel):
    """Response model for OAuth authorization URL"""

    authUrl: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Response model for OAuth callback"""

    success: bool
    message: str
    userId: str
    email: Optional[str] = None


class TokenStatusResponse(BaseModel):
    """Response model for token status"""

    hasToken: bool
    email: Optional[str] = None
    expiresAt: Optional[str] = None


class SentEmail(BaseModel):
    """Model for a sent email"""

    id: str
    userId: str
    subject: str
    body: str
    bodyType: str
    toRecipients: List[EmailAddress]
    ccRecipients: Optional[List[EmailAddress]] = None
    bccRecipients: Optional[List[EmailAddress]] = None
    importance: str
    outlookMessageId: Optional[str] = None
    outlookConversationId: Optional[str] = None
    trackingId: Optional[str] = None
    sentAt: str
    caseId: Optional[str] = None
    createdAt: str


class EmailReply(BaseModel):
    """Model for an email reply"""

    id: str
    sentEmailId: str
    outlookMessageId: str
    fromAddress: EmailAddress
    subject: str
    bodyPreview: str
    body: Optional[str] = None
    bodyType: str
    receivedAt: str
    isRead: bool
    hasAttachments: bool
    importance: str
    createdAt: str
    updatedAt: str


class SentEmailDetail(BaseModel):
    """Model for a sent email with its replies"""

    id: str
    userId: str
    subject: str
    body: str
    bodyType: str
    toRecipients: List[EmailAddress]
    ccRecipients: Optional[List[EmailAddress]] = None
    bccRecipients: Optional[List[EmailAddress]] = None
    importance: str
    outlookMessageId: Optional[str] = None
    outlookConversationId: Optional[str] = None
    trackingId: Optional[str] = None
    sentAt: str
    caseId: Optional[str] = None
    createdAt: str
    replies: List[EmailReply]


class SentEmailListResponse(BaseModel):
    """Response model for list of sent emails"""

    emails: List[SentEmail]
    total: int


class SyncRepliesResponse(BaseModel):
    """Response model for syncing replies"""

    success: bool
    message: str
    newReplies: int
    updatedReplies: int


class AddReplyRequest(BaseModel):
    """Request model for manually adding a reply"""

    outlookMessageId: str
    fromAddress: EmailAddress
    subject: str
    bodyPreview: str
    body: Optional[str] = None
    bodyType: Optional[str] = "HTML"
    receivedAt: str
    isRead: Optional[bool] = False
    hasAttachments: Optional[bool] = False
    importance: Optional[str] = "normal"


# Helper Functions
def get_msal_app():
    """Create and return MSAL confidential client application"""
    return msal.ConfidentialClientApplication(
        email_config.client_id,
        authority=email_config.authority,
        client_credential=email_config.client_secret,
    )


def build_woo_email_body(request: SendWOOEmailRequest) -> str:
    """
    Build HTML email body from WOO request template.

    Args:
        request: SendWOOEmailRequest containing template data

    Returns:
        HTML formatted email body
    """
    chunks_html = ""
    for chunk in request.chunks:
        page_info = f"Pagina {chunk.pageNumber}" if chunk.pageNumber else "Document"
        doc_info = f" ({chunk.documentId})" if chunk.documentId else ""
        chunks_html += f"<li><strong>{page_info}{doc_info}:</strong> {chunk.text}</li>"

    body = f"""<p>Beste {request.recipientName},</p>

            <p>We hebben een WOO verzoek gekregen over <strong>{request.requestDescription}</strong></p>

            <p>Je komt voor in de volgende teksten die openbaard zullen worden:</p>
            <ul>
            {chunks_html}
            </ul>

            <p>Zie de bijlage(n) voor de volledige documenten.</p>

            <p>Graag ontvangen we een reactie.</p>

            <p>Groeten,<br/>{request.senderName}</p>"""

    return body


def get_access_token(user_id: str) -> Optional[str]:
    """
    Get valid access token for user.
    Refreshes token if expired.
    """
    token_data = get_oauth_token(user_id)
    if not token_data:
        return None

    # Check if token is expired
    expires_at = token_data.get("expires_at", 0)
    if datetime.now().timestamp() < expires_at:
        return token_data["access_token"]

    # Token expired, try to refresh
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        return None

    try:
        app = get_msal_app()
        result = app.acquire_token_by_refresh_token(refresh_token, scopes=email_config.scopes)

        if "access_token" in result:
            # Update token in database
            new_expires_at = datetime.now().timestamp() + result.get("expires_in", 3600)
            save_oauth_token(
                user_id=user_id,
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token", refresh_token),
                expires_at=new_expires_at,
            )
            return result["access_token"]
    except Exception as e:
        logger.error(f"Failed to refresh token for user {user_id}: {e}")

    return None


def make_graph_request(
    user_id: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Make authenticated request to Microsoft Graph API.

    Args:
        user_id: User identifier
        endpoint: API endpoint (without base URL)
        method: HTTP method
        data: Request body data
        params: Query parameters

    Returns:
        Response data as dictionary

    Raises:
        HTTPException: If request fails or user not authenticated
    """
    access_token = get_access_token(user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="User not authenticated or token expired. Please authorize again.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    url = f"{email_config.graph_api_endpoint}/{endpoint}"

    try:
        response = requests.request(method=method, url=url, headers=headers, json=data, params=params)

        logger.debug(f"Graph API response status: {response.status_code}")

        if response.status_code >= 400:
            logger.error(f"Graph API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"Microsoft Graph API error: {response.text}")

        # Some endpoints return 202 Accepted or 204 No Content with empty body
        if response.status_code in (202, 204):
            logger.info(f"Graph API returned {response.status_code} with no content")
            return {"success": True}

        # For other success codes, try to parse JSON if there's content
        if not response.text or response.text.strip() == "":
            logger.info(f"Graph API returned {response.status_code} with empty body")
            return {"success": True}

        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}, Response text: {response.text}")
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from Microsoft Graph API: {str(e)}")

    except requests.RequestException as e:
        logger.error(f"Request to Graph API failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to communicate with Microsoft Graph API: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in make_graph_request: {e}")
        raise HTTPException(
            status_code=500, detail=f"Unexpected error communicating with Microsoft Graph API: {str(e)}"
        )


# API Endpoints
@email_router.get("/authorize", response_model=OAuthUrlResponse)
def get_authorization_url(user_id: str):
    """
    Generate Microsoft OAuth authorization URL.

    Args:
        user_id: User identifier to associate with the OAuth flow

    Returns:
        Authorization URL and state parameter
    """
    app = get_msal_app()

    # Generate authorization URL
    auth_url = app.get_authorization_request_url(
        scopes=email_config.scopes,
        redirect_uri=email_config.redirect_uri,
        state=user_id,  # Use user_id as state to track the user
    )

    logger.info(f"Generated authorization URL for user {user_id}")

    return OAuthUrlResponse(authUrl=auth_url, state=user_id)


@email_router.get("/callback", response_model=OAuthCallbackResponse)
def oauth_callback(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """
    Handle OAuth callback from Microsoft.

    Args:
        code: Authorization code from Microsoft
        state: State parameter (user_id)
        error: Error message if authorization failed

    Returns:
        Success status and user information
    """
    if error:
        logger.error(f"OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth authorization failed: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    user_id = state

    try:
        app = get_msal_app()

        # Acquire token using authorization code
        result = app.acquire_token_by_authorization_code(
            code, scopes=email_config.scopes, redirect_uri=email_config.redirect_uri
        )

        if "error" in result:
            logger.error(f"Token acquisition error: {result.get('error_description')}")
            raise HTTPException(status_code=400, detail=f"Failed to acquire token: {result.get('error_description')}")

        # Store tokens in database
        expires_at = datetime.now().timestamp() + result.get("expires_in", 3600)
        save_oauth_token(
            user_id=user_id,
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            expires_at=expires_at,
        )

        # Get user's email address
        user_info = make_graph_request(user_id, "me")
        email = user_info.get("mail") or user_info.get("userPrincipalName")

        logger.info(f"Successfully authenticated user {user_id} with email {email}")

        return OAuthCallbackResponse(
            success=True, message="Successfully authorized email access", userId=user_id, email=email
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@email_router.get("/status", response_model=TokenStatusResponse)
def get_token_status(user_id: str):
    """
    Check if user has valid email access token.

    Args:
        user_id: User identifier

    Returns:
        Token status and user email if available
    """
    token_data = get_oauth_token(user_id)
    if not token_data:
        return TokenStatusResponse(hasToken=False)

    expires_at = token_data.get("expires_at", 0)

    # Try to get user email
    email = None
    try:
        user_info = make_graph_request(user_id, "me")
        email = user_info.get("mail") or user_info.get("userPrincipalName")
    except:
        pass

    return TokenStatusResponse(
        hasToken=True, email=email, expiresAt=datetime.fromtimestamp(expires_at).isoformat() if expires_at else None
    )


@email_router.post("/send", response_model=SendEmailResponse)
def send_email(user_id: str, email_request: SendEmailRequest, case_id: Optional[str] = None):
    """
    Send an email via Microsoft Outlook.

    Args:
        user_id: User identifier
        email_request: Email content and recipients
        case_id: Optional case ID to associate with this email

    Returns:
        Success status and message ID
    """
    # Generate unique ID for this sent email
    sent_email_id = f"sent_{uuid.uuid4().hex[:12]}"

    # Generate tracking ID for subject line (shorter for readability)
    tracking_id = uuid.uuid4().hex[:8].upper()
    tracking_prefix = f"[WOO-{tracking_id}]"

    # Add tracking ID to subject
    tracked_subject = f"{tracking_prefix} {email_request.subject}"

    # Prepare email message
    message = {
        "message": {
            "subject": tracked_subject,
            "body": {"contentType": email_request.bodyType, "content": email_request.body},
            "toRecipients": [
                {"emailAddress": {"address": recipient.address, "name": recipient.name}}
                for recipient in email_request.to
            ],
            "importance": email_request.importance,
        },
        "saveToSentItems": True,  # Ensure email is saved to sent items
    }

    # Add CC recipients if provided
    if email_request.cc:
        message["message"]["ccRecipients"] = [
            {"emailAddress": {"address": recipient.address, "name": recipient.name}} for recipient in email_request.cc
        ]

    # Add BCC recipients if provided
    if email_request.bcc:
        message["message"]["bccRecipients"] = [
            {"emailAddress": {"address": recipient.address, "name": recipient.name}} for recipient in email_request.bcc
        ]

    # Add attachments if provided
    if email_request.attachments:
        attachments = []
        for attachment in email_request.attachments:
            attachment_data = {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": attachment.name,
                "contentType": attachment.contentType,
            }

            # Get content bytes - either from contentBytes or by reading from filePath
            content_bytes = attachment.contentBytes

            if not content_bytes and attachment.filePath:
                try:
                    file_path = Path(attachment.filePath)
                    if not file_path.exists():
                        raise HTTPException(status_code=400, detail=f"File not found: {attachment.filePath}")

                    # Read file and encode to base64
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                        content_bytes = base64.b64encode(file_content).decode("utf-8")

                    logger.info(f"Read attachment from file: {attachment.filePath}")
                except Exception as e:
                    logger.error(f"Failed to read attachment file {attachment.filePath}: {e}")
                    raise HTTPException(status_code=400, detail=f"Failed to read attachment file: {str(e)}")

            if not content_bytes:
                raise HTTPException(status_code=400, detail="Attachment must have either contentBytes or filePath")

            attachment_data["contentBytes"] = content_bytes
            attachments.append(attachment_data)

        message["message"]["attachments"] = attachments

    try:
        # Send email using Graph API
        result = make_graph_request(user_id=user_id, endpoint="me/sendMail", method="POST", data=message)

        logger.info(f"Email sent successfully by user {user_id}")

        # Try to retrieve the sent message from sent items to get Outlook IDs
        outlook_message_id = None
        outlook_conversation_id = None

        try:
            # Wait a moment for the email to appear in sent items
            import time

            time.sleep(1)

            # Search for the sent email by subject in sent items
            # Use the tracked subject (with prefix) for searching
            escaped_subject = tracked_subject.replace("'", "''")
            sent_messages = make_graph_request(
                user_id=user_id,
                endpoint="me/mailFolders/sentitems/messages",
                params={"$top": 1, "$orderby": "sentDateTime desc", "$filter": f"subject eq '{escaped_subject}'"},
            )

            if sent_messages.get("value") and len(sent_messages["value"]) > 0:
                sent_msg = sent_messages["value"][0]
                outlook_message_id = sent_msg.get("id")
                outlook_conversation_id = sent_msg.get("conversationId")
                logger.info(f"Retrieved Outlook message ID: {outlook_message_id}")
        except Exception as e:
            logger.warning(f"Could not retrieve sent message details: {e}")

        # Save sent email to database
        try:
            email_data = {
                "id": sent_email_id,
                "user_id": user_id,
                "subject": email_request.subject,  # Original subject without tracking ID
                "body": email_request.body,
                "body_type": email_request.bodyType,
                "to_recipients": [{"address": r.address, "name": r.name} for r in email_request.to],
                "cc_recipients": (
                    [{"address": r.address, "name": r.name} for r in email_request.cc] if email_request.cc else None
                ),
                "bcc_recipients": (
                    [{"address": r.address, "name": r.name} for r in email_request.bcc] if email_request.bcc else None
                ),
                "importance": email_request.importance,
                "outlook_message_id": outlook_message_id,
                "outlook_conversation_id": outlook_conversation_id,
                "tracking_id": tracking_id,  # Store the tracking ID for reply detection
                "sent_at": datetime.now().isoformat(),
                "case_id": case_id,
            }
            save_sent_email(email_data)
            logger.info(f"Saved sent email to database: {sent_email_id}")
        except Exception as e:
            logger.error(f"Failed to save sent email to database: {e}")
            # Don't fail the request if database save fails

        return SendEmailResponse(success=True, message="Email sent successfully", messageId=sent_email_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@email_router.post("/send/woo", response_model=SendEmailResponse)
def send_woo_email(user_id: str, email_request: SendWOOEmailRequest, case_id: Optional[str] = None):
    """
    Send a WOO (verzoek om inzage) email via Microsoft Outlook with template.

    The email body is automatically generated from the provided template fields
    (recipientName, requestDescription, chunks, senderName).

    Args:
        user_id: User identifier
        email_request: WOO email request with template data
        case_id: Optional case ID to associate with this email

    Returns:
        Success status and message ID
    """
    # Build the email body from template
    body = build_woo_email_body(email_request)

    # Convert SendWOOEmailRequest to SendEmailRequest
    send_request = SendEmailRequest(
        to=email_request.to,
        subject=email_request.subject,
        body=body,
        cc=email_request.cc,
        bcc=email_request.bcc,
        bodyType=email_request.bodyType,
        importance=email_request.importance,
        attachments=email_request.attachments,
    )

    # Use the existing send_email logic
    return send_email(user_id, send_request, case_id=case_id)


def build_stakeholder_email_body(
    stakeholder_id: str, case_id: str, content_type: str, custom_message: Optional[str] = None
) -> str:
    """
    Build email body based on stakeholder mentions and content type.

    Args:
        stakeholder_id: Stakeholder ID to filter mentions
        case_id: Case ID to get documents from
        content_type: "full_documents", "pages_only", or "chunks_only"
        custom_message: Optional custom message to include

    Returns:
        HTML formatted email body
    """
    # Get case and documents
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    document_ids = case.get("document_ids", [])
    if not document_ids:
        raise HTTPException(status_code=404, detail="No documents found for case")

    # Collect chunks with stakeholder mentions
    relevant_chunks = []
    relevant_pages = set()
    document_pages = {}  # Map document_id -> set of page numbers

    for doc_id in document_ids:
        chunks = get_chunks_by_document(doc_id)
        doc_pages = set()

        for chunk in chunks:
            chunk_stakeholders = get_chunk_stakeholders(chunk["id"])

            # Check if this chunk has a mention for our stakeholder
            has_stakeholder_mention = any(cs["stakeholder_id"] == stakeholder_id for cs in chunk_stakeholders)

            if has_stakeholder_mention:
                relevant_chunks.append({"chunk": chunk, "document_id": doc_id, "page": chunk["page"]})
                relevant_pages.add((doc_id, chunk["page"]))
                doc_pages.add(chunk["page"])

        if doc_pages:
            document_pages[doc_id] = doc_pages

    # Build email body based on content_type
    body_parts = []

    if custom_message:
        body_parts.append(f"<p>{custom_message}</p>")

    if content_type == "chunks_only":
        # Include only chunk text excerpts
        body_parts.append("<p>Je komt voor in de volgende teksten:</p>")
        body_parts.append("<ul>")

        for item in relevant_chunks:
            chunk = item["chunk"]
            doc = get_document_by_id(item["document_id"])
            doc_title = doc["title"] if doc else "Document"
            body_parts.append(
                f'<li><strong>{doc_title} (Pagina {chunk["page"]}):</strong> ' f'{chunk["context"][:200]}...</li>'
            )

        body_parts.append("</ul>")
        body_parts.append("<p>Zie de bijlage(n) voor de volledige documenten.</p>")

    elif content_type == "pages_only":
        # List which pages are included
        body_parts.append("<p>De volgende pagina's bevatten vermeldingen van jou:</p>")
        body_parts.append("<ul>")

        for doc_id, pages in document_pages.items():
            doc = get_document_by_id(doc_id)
            doc_title = doc["title"] if doc else "Document"
            pages_list = ", ".join(map(str, sorted(pages)))
            body_parts.append(f"<li><strong>{doc_title}:</strong> Pagina's {pages_list}</li>")

        body_parts.append("</ul>")
        body_parts.append("<p>Zie de bijlage(n) voor de relevante pagina's.</p>")

    else:  # full_documents
        # Just mention that full documents are attached
        body_parts.append("<p>De volledige documenten zijn als bijlage toegevoegd.</p>")

    return "".join(body_parts)


@email_router.post("/send/stakeholder", response_model=SendEmailResponse)
def send_stakeholder_email(request: SendStakeholderEmailRequest):
    """
    Send an email to a stakeholder based on their mentions in case documents.

    Args:
        request: Stakeholder email request with content type and recipients

    Returns:
        Success status and message ID
    """
    try:
        # Build email body based on content type
        email_body = build_stakeholder_email_body(
            stakeholder_id=request.stakeholder_id,
            case_id=request.case_id,
            content_type=request.content_type,
            custom_message=request.custom_message,
        )

        # Prepare attachments based on content_type
        attachments = []

        if request.content_type in ("full_documents", "pages_only"):
            # Get case documents
            case = get_case_by_id(request.case_id)
            if not case:
                raise HTTPException(status_code=404, detail="Case not found")

            document_ids = case.get("document_ids", [])

            # For full_documents, attach all PDFs
            # For pages_only, we'd need PDF manipulation (PyMuPDF) - simplified for now
            for doc_id in document_ids:
                doc = get_document_by_id(doc_id)
                if doc and doc.get("file_path"):
                    # Note: In production, you'd want to use PyMuPDF to extract pages
                    # For now, we'll attach the full document
                    file_path = Path(doc["file_path"])
                    if file_path.exists():
                        attachments.append(
                            EmailAttachment(name=file_path.name, contentType="application/pdf", filePath=str(file_path))
                        )

        # Create SendEmailRequest
        send_request = SendEmailRequest(
            to=request.to,
            subject=request.subject,
            body=email_body,
            cc=request.cc,
            bcc=request.bcc,
            bodyType="HTML",
            importance="normal",
            attachments=attachments if attachments else None,
        )

        # Send email using existing logic
        return send_email(request.user_id, send_request, case_id=request.case_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send stakeholder email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send stakeholder email: {str(e)}")


@email_router.get("/messages", response_model=EmailListResponse)
def get_emails(user_id: str, folder: str = "inbox", top: int = 10, skip: int = 0, filter_query: Optional[str] = None):
    """
    Read emails from user's mailbox.

    Args:
        user_id: User identifier
        folder: Mail folder (inbox, sentitems, drafts, etc.)
        top: Number of emails to return (max 100)
        skip: Number of emails to skip
        filter_query: OData filter query (e.g., "isRead eq false")

    Returns:
        List of email messages
    """
    # Validate and limit top parameter
    top = min(max(1, top), email_config.max_emails_per_request)

    # Build query parameters
    params = {
        "$top": top,
        "$skip": skip,
        "$select": "id,subject,bodyPreview,from,toRecipients,ccRecipients,receivedDateTime,isRead,hasAttachments,importance",
        "$orderby": "receivedDateTime desc",
    }

    if filter_query:
        params["$filter"] = filter_query

    try:
        # Get emails from Graph API
        endpoint = f"me/mailFolders/{folder}/messages"
        result = make_graph_request(user_id=user_id, endpoint=endpoint, params=params)

        # Parse email messages
        emails = []
        for item in result.get("value", []):
            from_addr = item.get("from", {}).get("emailAddress", {})
            to_recipients = [
                EmailAddress(
                    address=r.get("emailAddress", {}).get("address", ""), name=r.get("emailAddress", {}).get("name")
                )
                for r in item.get("toRecipients", [])
            ]
            cc_recipients = (
                [
                    EmailAddress(
                        address=r.get("emailAddress", {}).get("address", ""), name=r.get("emailAddress", {}).get("name")
                    )
                    for r in item.get("ccRecipients", [])
                ]
                if item.get("ccRecipients")
                else None
            )

            emails.append(
                EmailMessage(
                    id=item["id"],
                    subject=item.get("subject", ""),
                    bodyPreview=item.get("bodyPreview", ""),
                    from_address=EmailAddress(address=from_addr.get("address", ""), name=from_addr.get("name")),
                    toRecipients=to_recipients,
                    ccRecipients=cc_recipients,
                    receivedDateTime=item.get("receivedDateTime", ""),
                    isRead=item.get("isRead", False),
                    hasAttachments=item.get("hasAttachments", False),
                    importance=item.get("importance", "normal"),
                )
            )

        logger.info(f"Retrieved {len(emails)} emails for user {user_id}")

        return EmailListResponse(emails=emails, nextLink=result.get("@odata.nextLink"), total=len(emails))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve emails: {str(e)}")


@email_router.get("/messages/{message_id}")
def get_email_detail(user_id: str, message_id: str):
    """
    Get detailed information about a specific email.

    Args:
        user_id: User identifier
        message_id: Email message ID

    Returns:
        Detailed email information including full body
    """
    try:
        # Get email details from Graph API
        result = make_graph_request(user_id=user_id, endpoint=f"me/messages/{message_id}")

        from_addr = result.get("from", {}).get("emailAddress", {})
        to_recipients = [
            EmailAddress(
                address=r.get("emailAddress", {}).get("address", ""), name=r.get("emailAddress", {}).get("name")
            )
            for r in result.get("toRecipients", [])
        ]
        cc_recipients = (
            [
                EmailAddress(
                    address=r.get("emailAddress", {}).get("address", ""), name=r.get("emailAddress", {}).get("name")
                )
                for r in result.get("ccRecipients", [])
            ]
            if result.get("ccRecipients")
            else None
        )

        body_content = result.get("body", {}).get("content", "")

        email = EmailMessage(
            id=result["id"],
            subject=result.get("subject", ""),
            bodyPreview=result.get("bodyPreview", ""),
            body=body_content,
            from_address=EmailAddress(address=from_addr.get("address", ""), name=from_addr.get("name")),
            toRecipients=to_recipients,
            ccRecipients=cc_recipients,
            receivedDateTime=result.get("receivedDateTime", ""),
            isRead=result.get("isRead", False),
            hasAttachments=result.get("hasAttachments", False),
            importance=result.get("importance", "normal"),
        )

        logger.info(f"Retrieved email {message_id} for user {user_id}")

        return email

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve email details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve email details: {str(e)}")


@email_router.post("/messages/{message_id}/read")
def mark_email_as_read(user_id: str, message_id: str, is_read: bool = True):
    """
    Mark an email as read or unread.

    Args:
        user_id: User identifier
        message_id: Email message ID
        is_read: True to mark as read, False to mark as unread

    Returns:
        Success status
    """
    try:
        make_graph_request(
            user_id=user_id, endpoint=f"me/messages/{message_id}", method="PATCH", data={"isRead": is_read}
        )

        logger.info(f"Marked email {message_id} as {'read' if is_read else 'unread'} for user {user_id}")

        return {"success": True, "message": f"Email marked as {'read' if is_read else 'unread'}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update email status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update email status: {str(e)}")


@email_router.delete("/revoke")
def revoke_access(user_id: str):
    """
    Revoke email access for a user (remove stored tokens).

    Args:
        user_id: User identifier

    Returns:
        Success status
    """
    deleted = delete_oauth_token(user_id)
    if deleted:
        logger.info(f"Revoked email access for user {user_id}")
        return {"success": True, "message": "Email access revoked"}

    return {"success": True, "message": "No access to revoke"}


# ---------------------
# Sent Email Tracking Endpoints
# ---------------------


@email_router.get("/sent", response_model=SentEmailListResponse)
def get_sent_emails_list(user_id: Optional[str] = None, case_id: Optional[str] = None):
    """
    Get list of sent emails, optionally filtered by user_id or case_id.

    Args:
        user_id: Optional user identifier to filter by
        case_id: Optional case identifier to filter by

    Returns:
        List of sent emails
    """
    try:
        emails_data = get_sent_emails(user_id=user_id, case_id=case_id)

        emails = []
        for email_data in emails_data:
            emails.append(
                SentEmail(
                    id=email_data["id"],
                    userId=email_data["user_id"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    bodyType=email_data["body_type"],
                    toRecipients=[EmailAddress(**r) for r in email_data["to_recipients"]],
                    ccRecipients=(
                        [EmailAddress(**r) for r in email_data["cc_recipients"]]
                        if email_data.get("cc_recipients")
                        else None
                    ),
                    bccRecipients=(
                        [EmailAddress(**r) for r in email_data["bcc_recipients"]]
                        if email_data.get("bcc_recipients")
                        else None
                    ),
                    importance=email_data["importance"],
                    outlookMessageId=email_data.get("outlook_message_id"),
                    outlookConversationId=email_data.get("outlook_conversation_id"),
                    trackingId=email_data.get("tracking_id"),
                    sentAt=email_data["sent_at"],
                    caseId=email_data.get("case_id"),
                    createdAt=email_data["created_at"],
                )
            )

        logger.info(f"Retrieved {len(emails)} sent emails")

        return SentEmailListResponse(emails=emails, total=len(emails))

    except Exception as e:
        logger.error(f"Failed to retrieve sent emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sent emails: {str(e)}")


@email_router.get("/sent/{email_id}", response_model=SentEmailDetail)
def get_sent_email_detail(email_id: str):
    """
    Get detailed information about a sent email including all replies.

    Args:
        email_id: Sent email identifier

    Returns:
        Detailed sent email information with replies
    """
    try:
        email_data = get_sent_email_by_id(email_id)
        if not email_data:
            raise HTTPException(status_code=404, detail="Sent email not found")

        # Get replies for this email
        replies_data = get_email_replies(email_id)

        replies = []
        for reply_data in replies_data:
            replies.append(
                EmailReply(
                    id=reply_data["id"],
                    sentEmailId=reply_data["sent_email_id"],
                    outlookMessageId=reply_data["outlook_message_id"],
                    fromAddress=EmailAddress(**reply_data["from_address"]),
                    subject=reply_data["subject"],
                    bodyPreview=reply_data["body_preview"],
                    body=reply_data.get("body"),
                    bodyType=reply_data["body_type"],
                    receivedAt=reply_data["received_at"],
                    isRead=reply_data["is_read"],
                    hasAttachments=reply_data["has_attachments"],
                    importance=reply_data["importance"],
                    createdAt=reply_data["created_at"],
                    updatedAt=reply_data["updated_at"],
                )
            )

        sent_email = SentEmailDetail(
            id=email_data["id"],
            userId=email_data["user_id"],
            subject=email_data["subject"],
            body=email_data["body"],
            bodyType=email_data["body_type"],
            toRecipients=[EmailAddress(**r) for r in email_data["to_recipients"]],
            ccRecipients=(
                [EmailAddress(**r) for r in email_data["cc_recipients"]] if email_data.get("cc_recipients") else None
            ),
            bccRecipients=(
                [EmailAddress(**r) for r in email_data["bcc_recipients"]] if email_data.get("bcc_recipients") else None
            ),
            importance=email_data["importance"],
            outlookMessageId=email_data.get("outlook_message_id"),
            outlookConversationId=email_data.get("outlook_conversation_id"),
            trackingId=email_data.get("tracking_id"),
            sentAt=email_data["sent_at"],
            caseId=email_data.get("case_id"),
            createdAt=email_data["created_at"],
            replies=replies,
        )

        logger.info(f"Retrieved sent email {email_id} with {len(replies)} replies")

        return sent_email

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve sent email details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sent email details: {str(e)}")


@email_router.post("/sent/{email_id}/sync-replies", response_model=SyncRepliesResponse)
def sync_email_replies(email_id: str):
    """
    Sync replies from Outlook for a specific sent email.

    This endpoint fetches new replies from Outlook based on the conversation ID
    and saves them to the database.

    Args:
        email_id: Sent email identifier

    Returns:
        Sync status with counts of new and updated replies
    """
    try:
        # Get the sent email
        email_data = get_sent_email_by_id(email_id)
        if not email_data:
            raise HTTPException(status_code=404, detail="Sent email not found")

        conversation_id = email_data.get("outlook_conversation_id")
        user_id = email_data["user_id"]
        original_subject = email_data.get("subject", "")

        # Will be set if we find a conversation from inbox replies
        found_conversation_id = None

        if conversation_id:
            # Use conversation ID to find replies (preferred method)
            try:
                messages = make_graph_request(
                    user_id=user_id,
                    endpoint="me/messages",
                    params={
                        "$filter": f"conversationId eq '{conversation_id}'",
                        "$orderby": "receivedDateTime asc",
                        "$select": "id,subject,bodyPreview,body,from,receivedDateTime,isRead,hasAttachments,importance",
                    },
                )
            except HTTPException as e:
                # Handle authentication/authorization errors gracefully
                if e.status_code in (401, 403):
                    logger.info(f"User {user_id} not authenticated for Outlook access - cannot sync replies")
                    return SyncRepliesResponse(
                        success=True,
                        message="Cannot sync replies: user not authenticated with Outlook. Please authorize email access first.",
                        newReplies=0,
                        updatedReplies=0,
                    )
                else:
                    logger.warning(f"Graph API error while syncing conversation: {e.detail}")
                    return SyncRepliesResponse(
                        success=True, message=f"Could not sync replies: {e.detail}", newReplies=0, updatedReplies=0
                    )
            except Exception as e:
                logger.warning(f"Unexpected error while syncing conversation: {e}")
                return SyncRepliesResponse(
                    success=True, message="Could not sync replies (unexpected error)", newReplies=0, updatedReplies=0
                )
        else:
            # No conversation ID - search for emails containing the tracking ID
            try:
                tracking_id = email_data.get("tracking_id")
                if not tracking_id:
                    logger.warning(f"Email {email_id} has no tracking ID - cannot search for replies")
                    return SyncRepliesResponse(
                        success=True,
                        message="Cannot sync replies: email has no tracking ID",
                        newReplies=0,
                        updatedReplies=0,
                    )

                tracking_tag = f"[WOO-{tracking_id}]"
                logger.info(f"Searching for emails containing tracking tag: {tracking_tag}")

                # Search inbox for emails containing the tracking tag
                inbox_params = {
                    "$orderby": "receivedDateTime desc",
                    "$select": "id,conversationId,subject,bodyPreview,body,from,receivedDateTime,isRead,hasAttachments,importance",
                    "$top": 200,  # Get more emails to find all replies
                }

                # Use a simple search - we'll filter for the tracking tag in code
                inbox_messages = make_graph_request(
                    user_id=user_id, endpoint="me/mailFolders/inbox/messages", params=inbox_params
                )

                # Find all emails that contain the tracking tag in their subject
                conversation_messages = []
                inbox_count = len(inbox_messages.get("value", []))

                for msg in inbox_messages.get("value", []):
                    msg_subject = msg.get("subject", "")
                    if tracking_tag in msg_subject:
                        conversation_messages.append(msg)
                        logger.info(f"Found email in conversation: '{msg_subject}'")

                if not conversation_messages:
                    logger.info(f"No emails found with tracking tag {tracking_tag} in {inbox_count} inbox messages")
                    return SyncRepliesResponse(
                        success=True,
                        message=f"No emails found with tracking ID {tracking_id}. Checked {inbox_count} inbox messages.",
                        newReplies=0,
                        updatedReplies=0,
                    )

                # Sort messages by received time (oldest first)
                conversation_messages.sort(key=lambda x: x.get("receivedDateTime", ""))

                # Use the messages we found as the conversation
                messages = {"value": conversation_messages}
                logger.info(f"Found {len(conversation_messages)} emails in tracked conversation {tracking_id}")

            except HTTPException as e:
                # Handle authentication/authorization errors gracefully
                if e.status_code in (401, 403):
                    logger.info(f"User {user_id} not authenticated for Outlook access - cannot sync replies")
                    return SyncRepliesResponse(
                        success=True,
                        message="Cannot sync replies: user not authenticated with Outlook. Please authorize email access first.",
                        newReplies=0,
                        updatedReplies=0,
                    )
                else:
                    logger.warning(f"Graph API error while searching for tracking ID: {e.detail}")
                    return SyncRepliesResponse(
                        success=True,
                        message=f"Could not search for replies: {e.detail}",
                        newReplies=0,
                        updatedReplies=0,
                    )
            except Exception as e:
                logger.warning(f"Unexpected error while searching for tracking ID: {e}")
                return SyncRepliesResponse(
                    success=True,
                    message="Could not search for replies (unexpected error)",
                    newReplies=0,
                    updatedReplies=0,
                )

        new_replies = 0
        updated_replies = 0

        # Process each message in the conversation
        for msg in messages.get("value", []):
            msg_id = msg.get("id")

            # Skip if this is the original sent message
            if msg_id == email_data.get("outlook_message_id"):
                continue

            # Check if reply already exists
            existing_reply = get_email_reply_by_outlook_id(msg_id)

            from_addr = msg.get("from", {}).get("emailAddress", {})
            body_content = msg.get("body", {})

            reply_data = {
                "id": f"reply_{uuid.uuid4().hex[:12]}",
                "sent_email_id": email_id,
                "outlook_message_id": msg_id,
                "from_address": {"address": from_addr.get("address", ""), "name": from_addr.get("name")},
                "subject": msg.get("subject", ""),
                "body_preview": msg.get("bodyPreview", ""),
                "body": body_content.get("content", ""),
                "body_type": body_content.get("contentType", "HTML"),
                "received_at": msg.get("receivedDateTime", ""),
                "is_read": msg.get("isRead", False),
                "has_attachments": msg.get("hasAttachments", False),
                "importance": msg.get("importance", "normal"),
            }

            if existing_reply:
                updated_replies += 1
            else:
                new_replies += 1

            save_email_reply(reply_data)

        logger.info(f"Synced replies for email {email_id}: {new_replies} new, {updated_replies} updated")

        return SyncRepliesResponse(
            success=True,
            message=f"Successfully synced replies: {new_replies} new, {updated_replies} updated",
            newReplies=new_replies,
            updatedReplies=updated_replies,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync email replies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync email replies: {str(e)}")


@email_router.post("/sent/sync-all-replies", response_model=SyncRepliesResponse)
def sync_all_email_replies(user_id: str):
    """
    Sync replies from Outlook for all sent emails by a user.

    This endpoint fetches new replies from Outlook for all sent emails
    that have a conversation ID and saves them to the database.

    Args:
        user_id: User identifier

    Returns:
        Sync status with total counts of new and updated replies
    """
    try:
        # Get all sent emails for this user
        emails_data = get_sent_emails(user_id=user_id)

        total_new = 0
        total_updated = 0
        synced_count = 0

        for email_data in emails_data:
            conversation_id = email_data.get("outlook_conversation_id")
            if not conversation_id:
                continue

            email_id = email_data["id"]

            try:
                # Fetch messages in this conversation from Outlook
                messages = make_graph_request(
                    user_id=user_id,
                    endpoint="me/messages",
                    params={
                        "$filter": f"conversationId eq '{conversation_id}'",
                        "$orderby": "receivedDateTime asc",
                        "$select": "id,subject,bodyPreview,body,from,receivedDateTime,isRead,hasAttachments,importance",
                    },
                )

                # Process each message in the conversation
                for msg in messages.get("value", []):
                    msg_id = msg.get("id")

                    # Skip if this is the original sent message
                    if msg_id == email_data.get("outlook_message_id"):
                        continue

                    # Check if reply already exists
                    existing_reply = get_email_reply_by_outlook_id(msg_id)

                    from_addr = msg.get("from", {}).get("emailAddress", {})
                    body_content = msg.get("body", {})

                    reply_data = {
                        "id": f"reply_{uuid.uuid4().hex[:12]}",
                        "sent_email_id": email_id,
                        "outlook_message_id": msg_id,
                        "from_address": {"address": from_addr.get("address", ""), "name": from_addr.get("name")},
                        "subject": msg.get("subject", ""),
                        "body_preview": msg.get("bodyPreview", ""),
                        "body": body_content.get("content", ""),
                        "body_type": body_content.get("contentType", "HTML"),
                        "received_at": msg.get("receivedDateTime", ""),
                        "is_read": msg.get("isRead", False),
                        "has_attachments": msg.get("hasAttachments", False),
                        "importance": msg.get("importance", "normal"),
                    }

                    if existing_reply:
                        total_updated += 1
                    else:
                        total_new += 1

                    save_email_reply(reply_data)

                synced_count += 1

            except Exception as e:
                logger.warning(f"Failed to sync replies for email {email_id}: {e}")
                continue

        logger.info(f"Synced replies for {synced_count} emails: {total_new} new, {total_updated} updated")

        return SyncRepliesResponse(
            success=True,
            message=f"Successfully synced {synced_count} email conversations: {total_new} new replies, {total_updated} updated",
            newReplies=total_new,
            updatedReplies=total_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync all email replies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync all email replies: {str(e)}")


@email_router.get("/inbox/messages", response_model=EmailListResponse)
def get_inbox_messages(user_id: str, top: int = 10, filter_replies: Optional[str] = None):
    """
    Get recent inbox messages for debugging reply detection.

    Args:
        user_id: User identifier
        top: Number of messages to return (max 50)
        filter_replies: If provided, only show messages that start with "Re: [filter_replies]"

    Returns:
        List of inbox messages
    """
    try:
        top = min(max(1, top), 50)  # Limit to reasonable range

        params = {
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,bodyPreview,from,toRecipients,ccRecipients,receivedDateTime,isRead,hasAttachments,importance",
            "$top": top,
        }

        result = make_graph_request(user_id=user_id, endpoint="me/mailFolders/inbox/messages", params=params)

        # Filter messages if requested
        messages = result.get("value", [])
        if filter_replies:
            filter_subject = f"Re: {filter_replies}"
            messages = [msg for msg in messages if msg.get("subject", "").startswith(filter_subject)]

        # Convert to EmailMessage format
        emails = []
        for item in messages:
            from_addr = item.get("from", {}).get("emailAddress", {})
            to_recipients = [
                EmailAddress(
                    address=r.get("emailAddress", {}).get("address", ""), name=r.get("emailAddress", {}).get("name")
                )
                for r in item.get("toRecipients", [])
            ]
            cc_recipients = (
                [
                    EmailAddress(
                        address=r.get("emailAddress", {}).get("address", ""), name=r.get("emailAddress", {}).get("name")
                    )
                    for r in item.get("ccRecipients", [])
                ]
                if item.get("ccRecipients")
                else None
            )

            emails.append(
                EmailMessage(
                    id=item["id"],
                    subject=item.get("subject", ""),
                    bodyPreview=item.get("bodyPreview", ""),
                    from_address=EmailAddress(address=from_addr.get("address", ""), name=from_addr.get("name")),
                    toRecipients=to_recipients,
                    ccRecipients=cc_recipients,
                    receivedDateTime=item.get("receivedDateTime", ""),
                    isRead=item.get("isRead", False),
                    hasAttachments=item.get("hasAttachments", False),
                    importance=item.get("importance", "normal"),
                )
            )

        logger.info(f"Retrieved {len(emails)} inbox messages for user {user_id}")

        return EmailListResponse(
            emails=emails, nextLink=None, total=len(emails)  # Not implementing pagination for debug endpoint
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve inbox messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve inbox messages: {str(e)}")


@email_router.post("/sent/{email_id}/add-reply", response_model=SyncRepliesResponse)
def add_manual_reply(email_id: str, reply_request: AddReplyRequest):
    """
    Manually add a reply to a sent email.

    This is useful for testing or when you want to add replies that weren't
    automatically detected by the sync process.

    Args:
        email_id: Sent email identifier
        reply_request: Reply details

    Returns:
        Success status
    """
    try:
        # Get the sent email
        email_data = get_sent_email_by_id(email_id)
        if not email_data:
            raise HTTPException(status_code=404, detail="Sent email not found")

        # Check if reply already exists
        existing_reply = get_email_reply_by_outlook_id(reply_request.outlookMessageId)
        if existing_reply:
            return SyncRepliesResponse(
                success=False,
                message="Reply with this Outlook message ID already exists",
                newReplies=0,
                updatedReplies=0,
            )

        # Create reply data
        reply_data = {
            "id": f"reply_{uuid.uuid4().hex[:12]}",
            "sent_email_id": email_id,
            "outlook_message_id": reply_request.outlookMessageId,
            "from_address": {"address": reply_request.fromAddress.address, "name": reply_request.fromAddress.name},
            "subject": reply_request.subject,
            "body_preview": reply_request.bodyPreview,
            "body": reply_request.body,
            "body_type": reply_request.bodyType,
            "received_at": reply_request.receivedAt,
            "is_read": reply_request.isRead,
            "has_attachments": reply_request.hasAttachments,
            "importance": reply_request.importance,
        }

        # Save the reply
        save_email_reply(reply_data)

        logger.info(f"Manually added reply {reply_data['id']} to email {email_id}")

        return SyncRepliesResponse(success=True, message="Reply added successfully", newReplies=1, updatedReplies=0)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add manual reply: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add reply: {str(e)}")


# Export router for integration with main app
__all__ = ["email_router"]
