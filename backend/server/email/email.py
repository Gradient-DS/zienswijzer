"""
Email integration with Microsoft Outlook using Graph API.

This module provides OAuth authentication and email operations (send, read)
for Microsoft Outlook accounts using the Microsoft Graph API.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import msal
import requests
import logging
import base64
from pathlib import Path

from .config import email_config
from ..db.database import get_oauth_token, save_oauth_token, delete_oauth_token

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
                expires_at=new_expires_at
            )
            return result["access_token"]
    except Exception as e:
        logger.error(f"Failed to refresh token for user {user_id}: {e}")
    
    return None


def make_graph_request(
    user_id: str,
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
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
        raise HTTPException(
            status_code=401,
            detail="User not authenticated or token expired. Please authorize again."
        )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    url = f"{email_config.graph_api_endpoint}/{endpoint}"
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        )
        
        logger.debug(f"Graph API response status: {response.status_code}")
        
        if response.status_code >= 400:
            logger.error(f"Graph API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Microsoft Graph API error: {response.text}"
            )
        
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
            raise HTTPException(
                status_code=500,
                detail=f"Invalid JSON response from Microsoft Graph API: {str(e)}"
            )
    
    except requests.RequestException as e:
        logger.error(f"Request to Graph API failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to communicate with Microsoft Graph API: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in make_graph_request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error communicating with Microsoft Graph API: {str(e)}"
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
        state=user_id  # Use user_id as state to track the user
    )
    
    logger.info(f"Generated authorization URL for user {user_id}")
    
    return OAuthUrlResponse(
        authUrl=auth_url,
        state=user_id
    )


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
            code,
            scopes=email_config.scopes,
            redirect_uri=email_config.redirect_uri
        )
        
        if "error" in result:
            logger.error(f"Token acquisition error: {result.get('error_description')}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to acquire token: {result.get('error_description')}"
            )
        
        # Store tokens in database
        expires_at = datetime.now().timestamp() + result.get("expires_in", 3600)
        save_oauth_token(
            user_id=user_id,
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            expires_at=expires_at
        )
        
        # Get user's email address
        user_info = make_graph_request(user_id, "me")
        email = user_info.get("mail") or user_info.get("userPrincipalName")
        
        logger.info(f"Successfully authenticated user {user_id} with email {email}")
        
        return OAuthCallbackResponse(
            success=True,
            message="Successfully authorized email access",
            userId=user_id,
            email=email
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
        hasToken=True,
        email=email,
        expiresAt=datetime.fromtimestamp(expires_at).isoformat() if expires_at else None
    )


@email_router.post("/send", response_model=SendEmailResponse)
def send_email(user_id: str, email_request: SendEmailRequest):
    """
    Send an email via Microsoft Outlook.
    
    Args:
        user_id: User identifier
        email_request: Email content and recipients
    
    Returns:
        Success status and message ID
    """
    # Prepare email message
    message = {
        "message": {
            "subject": email_request.subject,
            "body": {
                "contentType": email_request.bodyType,
                "content": email_request.body
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient.address, "name": recipient.name}}
                for recipient in email_request.to
            ],
            "importance": email_request.importance
        }
    }
    
    # Add CC recipients if provided
    if email_request.cc:
        message["message"]["ccRecipients"] = [
            {"emailAddress": {"address": recipient.address, "name": recipient.name}}
            for recipient in email_request.cc
        ]
    
    # Add BCC recipients if provided
    if email_request.bcc:
        message["message"]["bccRecipients"] = [
            {"emailAddress": {"address": recipient.address, "name": recipient.name}}
            for recipient in email_request.bcc
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
                        raise HTTPException(
                            status_code=400,
                            detail=f"File not found: {attachment.filePath}"
                        )
                    
                    # Read file and encode to base64
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                        content_bytes = base64.b64encode(file_content).decode("utf-8")
                    
                    logger.info(f"Read attachment from file: {attachment.filePath}")
                except Exception as e:
                    logger.error(f"Failed to read attachment file {attachment.filePath}: {e}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to read attachment file: {str(e)}"
                    )
            
            if not content_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="Attachment must have either contentBytes or filePath"
                )
            
            attachment_data["contentBytes"] = content_bytes
            attachments.append(attachment_data)
        
        message["message"]["attachments"] = attachments
    
    try:
        # Send email using Graph API
        result = make_graph_request(
            user_id=user_id,
            endpoint="me/sendMail",
            method="POST",
            data=message
        )
        
        logger.info(f"Email sent successfully by user {user_id}")
        
        return SendEmailResponse(
            success=True,
            message="Email sent successfully",
            messageId=None  # sendMail endpoint doesn't return message ID
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@email_router.post("/send/woo", response_model=SendEmailResponse)
def send_woo_email(user_id: str, email_request: SendWOOEmailRequest):
    """
    Send a WOO (verzoek om inzage) email via Microsoft Outlook with template.
    
    The email body is automatically generated from the provided template fields
    (recipientName, requestDescription, chunks, senderName).
    
    Args:
        user_id: User identifier
        email_request: WOO email request with template data
    
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
        attachments=email_request.attachments
    )
    
    # Use the existing send_email logic
    return send_email(user_id, send_request)


@email_router.get("/messages", response_model=EmailListResponse)
def get_emails(
    user_id: str,
    folder: str = "inbox",
    top: int = 10,
    skip: int = 0,
    filter_query: Optional[str] = None
):
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
        "$orderby": "receivedDateTime desc"
    }
    
    if filter_query:
        params["$filter"] = filter_query
    
    try:
        # Get emails from Graph API
        endpoint = f"me/mailFolders/{folder}/messages"
        result = make_graph_request(
            user_id=user_id,
            endpoint=endpoint,
            params=params
        )
        
        # Parse email messages
        emails = []
        for item in result.get("value", []):
            from_addr = item.get("from", {}).get("emailAddress", {})
            to_recipients = [
                EmailAddress(
                    address=r.get("emailAddress", {}).get("address", ""),
                    name=r.get("emailAddress", {}).get("name")
                )
                for r in item.get("toRecipients", [])
            ]
            cc_recipients = [
                EmailAddress(
                    address=r.get("emailAddress", {}).get("address", ""),
                    name=r.get("emailAddress", {}).get("name")
                )
                for r in item.get("ccRecipients", [])
            ] if item.get("ccRecipients") else None
            
            emails.append(EmailMessage(
                id=item["id"],
                subject=item.get("subject", ""),
                bodyPreview=item.get("bodyPreview", ""),
                from_address=EmailAddress(
                    address=from_addr.get("address", ""),
                    name=from_addr.get("name")
                ),
                toRecipients=to_recipients,
                ccRecipients=cc_recipients,
                receivedDateTime=item.get("receivedDateTime", ""),
                isRead=item.get("isRead", False),
                hasAttachments=item.get("hasAttachments", False),
                importance=item.get("importance", "normal")
            ))
        
        logger.info(f"Retrieved {len(emails)} emails for user {user_id}")
        
        return EmailListResponse(
            emails=emails,
            nextLink=result.get("@odata.nextLink"),
            total=len(emails)
        )
    
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
        result = make_graph_request(
            user_id=user_id,
            endpoint=f"me/messages/{message_id}"
        )
        
        from_addr = result.get("from", {}).get("emailAddress", {})
        to_recipients = [
            EmailAddress(
                address=r.get("emailAddress", {}).get("address", ""),
                name=r.get("emailAddress", {}).get("name")
            )
            for r in result.get("toRecipients", [])
        ]
        cc_recipients = [
            EmailAddress(
                address=r.get("emailAddress", {}).get("address", ""),
                name=r.get("emailAddress", {}).get("name")
            )
            for r in result.get("ccRecipients", [])
        ] if result.get("ccRecipients") else None
        
        body_content = result.get("body", {}).get("content", "")
        
        email = EmailMessage(
            id=result["id"],
            subject=result.get("subject", ""),
            bodyPreview=result.get("bodyPreview", ""),
            body=body_content,
            from_address=EmailAddress(
                address=from_addr.get("address", ""),
                name=from_addr.get("name")
            ),
            toRecipients=to_recipients,
            ccRecipients=cc_recipients,
            receivedDateTime=result.get("receivedDateTime", ""),
            isRead=result.get("isRead", False),
            hasAttachments=result.get("hasAttachments", False),
            importance=result.get("importance", "normal")
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
            user_id=user_id,
            endpoint=f"me/messages/{message_id}",
            method="PATCH",
            data={"isRead": is_read}
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


# Export router for integration with main app
__all__ = ["email_router"]

