# Email Integration with Microsoft Outlook

This module provides integration with Microsoft Outlook using the Microsoft Graph API, enabling users to authorize email access, send emails, and read emails.

## Features

- **OAuth 2.0 Authentication**: Secure authorization flow for Microsoft accounts
- **Send Emails**: Send emails with support for CC, BCC, attachments, and HTML/text content
- **Read Emails**: Fetch emails from various folders (inbox, sent items, etc.)
- **Email Details**: Get full email content including body and metadata
- **Mark as Read/Unread**: Update email read status
- **Token Management**: Automatic token refresh and storage

## Prerequisites

### 1. Register an App in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in the details:
   - **Name**: Your app name (e.g., "WOO Email Integration")
   - **Supported account types**: Accounts in any organizational directory and personal Microsoft accounts
   - **Redirect URI**: Select "Web" and enter `http://localhost:8000/email/callback` (adjust for production)
5. Click **Register**

### 2. Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** > **Microsoft Graph** > **Delegated permissions**
3. Add the following permissions:
   - `User.Read`
   - `Mail.Read`
   - `Mail.Send`
   - `Mail.ReadWrite`
4. Click **Grant admin consent** (if required by your organization)

### 3. Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and set expiration
4. Copy the **Value** (you won't be able to see it again!)

### 4. Note Your Credentials

You'll need:
- **Application (client) ID**: Found on the app's overview page
- **Client secret**: The value you just copied
- **Redirect URI**: The callback URL you configured

## Installation

### Required Python Packages

Add these to your `requirements.txt`:

```txt
msal>=1.24.0
requests>=2.31.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Set the following environment variables (create a `.env` file):

```bash
# Microsoft Graph API Credentials
MICROSOFT_CLIENT_ID=your-application-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_REDIRECT_URI=http://localhost:8000/email/callback
```

**Important**: Never commit these credentials to version control!

## Integration with FastAPI

To integrate this module with your main `app.py`:

```python
from fastapi import FastAPI
from server.email import email_router

app = FastAPI(title="WOO Backend", version="0.1.0")

# Include email router
app.include_router(email_router)
```

## API Endpoints

All endpoints are prefixed with `/email`.

### Quick Reference

| # | Endpoint | Method | Purpose | Database Updates |
|---|----------|--------|---------|------------------|
| 1 | `/authorize` | GET | Generate OAuth URL | None |
| 2 | `/callback` | GET | Handle OAuth callback | OAuthTokens (insert/update) |
| 3 | `/status` | GET | Check token status | None (read-only) |
| 4 | `/revoke` | DELETE | Revoke email access | OAuthTokens (delete) |
| 5 | `/send` | POST | Send email | SentEmails (insert) |
| 6 | `/send/woo` | POST | Send WOO email with template | SentEmails (insert) |
| 7 | `/messages` | GET | Get emails from mailbox | None (Graph API only) |
| 8 | `/messages/{message_id}` | GET | Get email details | None (Graph API only) |
| 9 | `/messages/{message_id}/read` | POST | Mark email as read/unread | None (Graph API only) |
| 10 | `/sent` | GET | Get sent emails list | None (read-only) |
| 11 | `/sent/{email_id}` | GET | Get sent email detail | None (read-only) |
| 12 | `/sent/{email_id}/sync-replies` | POST | Sync replies for one email | EmailReplies (insert/update) |
| 13 | `/sent/sync-all-replies` | POST | Sync all replies for user | EmailReplies (insert/update) |
| 14 | `/inbox/messages` | GET | Debug: Get inbox messages | None (Graph API only) |
| 15 | `/sent/{email_id}/add-reply` | POST | Manually add reply | EmailReplies (insert) |

---

### Authentication Endpoints

---

#### 1. Get Authorization URL
**Endpoint:** `GET /email/authorize`

**What it does:**  
Generates a Microsoft OAuth authorization URL that users can visit to grant email access.

**Input Parameters:**
- `user_id` (query, required): User identifier (e.g., `test_user_123`)

**Returns:**
```json
{
  "authUrl": "https://login.microsoftonline.com/...",
  "state": "test_user_123"
}
```

**Database Updates:**  
None - only generates URL.

**Example curl command:**
```bash
curl -X GET "http://localhost:8000/email/authorize?user_id=test_user_123"
```

---

#### 2. OAuth Callback (Automatic)
**Endpoint:** `GET /email/callback`

**What it does:**  
Handles the OAuth callback from Microsoft after user authorization. Exchanges authorization code for access/refresh tokens and stores them.

**Input Parameters:**
- `code` (query, required): Authorization code from Microsoft
- `state` (query, required): State parameter (user_id)
- `error` (query, optional): Error message if authorization failed

**Returns:**
```json
{
  "success": true,
  "message": "Successfully authorized email access",
  "userId": "test_user_123",
  "email": "user@example.com"
}
```

**Database Updates:**  
Inserts/updates a row in the `OAuthTokens` table:
- `user_id`: User identifier
- `access_token`: OAuth access token
- `refresh_token`: OAuth refresh token
- `expires_at`: Token expiration timestamp
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Example curl command:**
```bash
# This endpoint is typically called automatically by Microsoft OAuth flow
# Manual call would look like:
curl -X GET "http://localhost:8000/email/callback?code=AUTHORIZATION_CODE&state=test_user_123"
```

---

#### 3. Check Token Status
**Endpoint:** `GET /email/status`

**What it does:**  
Checks if a user has a valid OAuth token and returns their email address.

**Input Parameters:**
- `user_id` (query, required): User identifier

**Returns:**
```json
{
  "hasToken": true,
  "email": "user@example.com",
  "expiresAt": "2025-10-31T12:00:00"
}
```

**Database Updates:**  
None - read-only query from `OAuthTokens` table.

**Example curl command:**
```bash
curl -X GET "http://localhost:8000/email/status?user_id=test_user_123"
```

---

#### 4. Revoke Access
**Endpoint:** `DELETE /email/revoke`

**What it does:**  
Revokes email access by removing stored OAuth tokens for a user.

**Input Parameters:**
- `user_id` (query, required): User identifier

**Returns:**
```json
{
  "success": true,
  "message": "Email access revoked"
}
```

**Database Updates:**  
Deletes the row from `OAuthTokens` table where `user_id` matches.

**Example curl command:**
```bash
curl -X DELETE "http://localhost:8000/email/revoke?user_id=test_user_123"
```

---

### Email Operations

---

#### 5. Send Email
**Endpoint:** `POST /email/send`

**What it does:**  
Sends an email via Microsoft Outlook with support for CC, BCC, attachments, and HTML/text content. Automatically adds a tracking ID to the subject for reply detection.

**Input Parameters:**
- `user_id` (query, required): User identifier
- `case_id` (query, optional): Case ID to associate with this email
- **Request body (JSON):**
  ```json
  {
    "to": [
      {
        "address": "recipient@example.com",
        "name": "Recipient Name"
      }
    ],
    "subject": "Email Subject",
    "body": "<h1>Hello</h1><p>This is an HTML email</p>",
    "bodyType": "HTML",
    "importance": "normal",
    "cc": [],
    "bcc": [],
    "attachments": []
  }
  ```

**Returns:**
```json
{
  "success": true,
  "message": "Email sent successfully",
  "messageId": "sent_abc123def456"
}
```

**Database Updates:**  
Inserts a row in the `SentEmails` table:
- `id`: Generated sent email ID
- `user_id`: User identifier
- `subject`: Email subject (without tracking ID)
- `body`: Email body content
- `body_type`: "HTML" or "Text"
- `to_recipients`: JSON array of recipients
- `cc_recipients`: JSON array of CC recipients (if any)
- `bcc_recipients`: JSON array of BCC recipients (if any)
- `importance`: Email importance
- `outlook_message_id`: Outlook message ID (if retrieved)
- `outlook_conversation_id`: Outlook conversation ID (if retrieved)
- `tracking_id`: 8-character tracking ID
- `sent_at`: Timestamp when sent
- `case_id`: Associated case ID (if provided)
- `created_at`: Timestamp

**Example curl command:**
```bash
curl -X POST "http://localhost:8000/email/send?user_id=test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "to": [
      {
        "address": "recipient@example.com",
        "name": "John Doe"
      }
    ],
    "subject": "Test Email",
    "body": "<p>This is a test email</p>",
    "bodyType": "HTML",
    "importance": "normal"
  }'
```

---

#### 6. Send WOO Email (with Template)
**Endpoint:** `POST /email/send/woo`

**What it does:**  
Sends a WOO (Wet Openbaarheid van Bestuur) email using a predefined Dutch government template. Automatically generates email body from template fields.

**Input Parameters:**
- `user_id` (query, required): User identifier
- `case_id` (query, optional): Case ID to associate with this email
- **Request body (JSON):**
  ```json
  {
    "to": [{"address": "stakeholder@example.com", "name": "John Doe"}],
    "subject": "WOO Verzoek - Inzage",
    "requestDescription": "documenten over project X",
    "recipientName": "John Doe",
    "senderName": "Jane Smith",
    "chunks": [
      {
        "id": "chunk_1",
        "text": "This text mentions the stakeholder",
        "pageNumber": 5,
        "documentId": "doc_123"
      }
    ],
    "cc": [],
    "bcc": [],
    "attachments": []
  }
  ```

**Returns:**
```json
{
  "success": true,
  "message": "Email sent successfully",
  "messageId": "sent_abc123def456"
}
```

**Database Updates:**  
Same as "Send Email" endpoint - inserts a row in the `SentEmails` table.

**Example curl command:**
```bash
curl -X POST "http://localhost:8000/email/send/woo?user_id=test_user_123&case_id=case_789" \
  -H "Content-Type: application/json" \
  -d '{
    "to": [{"address": "stakeholder@example.com", "name": "John Doe"}],
    "subject": "WOO Verzoek - Inzage Project X",
    "requestDescription": "documenten over project X",
    "recipientName": "John Doe",
    "senderName": "Jane Smith",
    "chunks": [
      {
        "id": "chunk_1",
        "text": "Your name appears in this section",
        "pageNumber": 5,
        "documentId": "doc_123"
      }
    ]
  }'
```

---

#### 7. Get Emails
**Endpoint:** `GET /email/messages`

**What it does:**  
Retrieves emails from a specified folder in the user's mailbox with pagination and filtering support.

**Input Parameters:**
- `user_id` (query, required): User identifier
- `folder` (query, optional, default: "inbox"): Mail folder
  - Options: "inbox", "sentitems", "drafts", "deleteditems", "junkemail"
- `top` (query, optional, default: 10, max: 100): Number of emails to return
- `skip` (query, optional, default: 0): Number of emails to skip (pagination)
- `filter_query` (query, optional): OData filter (e.g., "isRead eq false")

**Returns:**
```json
{
  "emails": [
    {
      "id": "AAMkADU...",
      "subject": "Email Subject",
      "bodyPreview": "Preview of email content...",
      "from_address": {
        "address": "sender@example.com",
        "name": "Sender Name"
      },
      "toRecipients": [{"address": "...", "name": "..."}],
      "ccRecipients": null,
      "receivedDateTime": "2025-10-31T10:00:00Z",
      "isRead": false,
      "hasAttachments": false,
      "importance": "normal"
    }
  ],
  "nextLink": null,
  "total": 1
}
```

**Database Updates:**  
None - read-only query to Microsoft Graph API.

**Example curl command:**
```bash
# Get 10 unread emails from inbox
curl -X GET "http://localhost:8000/email/messages?user_id=test_user_123&folder=inbox&top=10&filter_query=isRead%20eq%20false"
```

---

#### 8. Get Email Details
**Endpoint:** `GET /email/messages/{message_id}`

**What it does:**  
Retrieves detailed information about a specific email including the full body content.

**Input Parameters:**
- `message_id` (path, required): Email message ID from Outlook
- `user_id` (query, required): User identifier

**Returns:**
```json
{
  "id": "AAMkADU...",
  "subject": "Email Subject",
  "bodyPreview": "Preview...",
  "body": "<html><body>Full email body...</body></html>",
  "from_address": {"address": "sender@example.com", "name": "Sender"},
  "toRecipients": [{"address": "...", "name": "..."}],
  "ccRecipients": null,
  "receivedDateTime": "2025-10-31T10:00:00Z",
  "isRead": false,
  "hasAttachments": false,
  "importance": "normal"
}
```

**Database Updates:**  
None - read-only query to Microsoft Graph API.

**Example curl command:**
```bash
curl -X GET "http://localhost:8000/email/messages/AAMkADUyMzYxNjU...?user_id=test_user_123"
```

---

#### 9. Mark Email as Read/Unread
**Endpoint:** `POST /email/messages/{message_id}/read`

**What it does:**  
Marks an email in Outlook as read or unread.

**Input Parameters:**
- `message_id` (path, required): Email message ID from Outlook
- `user_id` (query, required): User identifier
- `is_read` (query, optional, default: true): True to mark as read, false to mark as unread

**Returns:**
```json
{
  "success": true,
  "message": "Email marked as read"
}
```

**Database Updates:**  
None - updates email status in Microsoft Graph API only.

**Example curl command:**
```bash
# Mark as read
curl -X POST "http://localhost:8000/email/messages/AAMkADUyMzYxNjU.../read?user_id=test_user_123&is_read=true"

# Mark as unread
curl -X POST "http://localhost:8000/email/messages/AAMkADUyMzYxNjU.../read?user_id=test_user_123&is_read=false"
```

---

### Sent Email Tracking Endpoints

---

#### 10. Get Sent Emails
**Endpoint:** `GET /email/sent`

**What it does:**  
Retrieves a list of sent emails from the database, optionally filtered by user or case.

**Input Parameters:**
- `user_id` (query, optional): Filter by user identifier
- `case_id` (query, optional): Filter by case identifier

**Returns:**
```json
{
  "emails": [
    {
      "id": "sent_abc123def456",
      "userId": "test_user_123",
      "subject": "Test Email",
      "body": "<p>Email content</p>",
      "bodyType": "HTML",
      "toRecipients": [{"address": "...", "name": "..."}],
      "ccRecipients": null,
      "bccRecipients": null,
      "importance": "normal",
      "outlookMessageId": "AAMkADU...",
      "outlookConversationId": "AAQkADU...",
      "trackingId": "A1B2C3D4",
      "sentAt": "2025-10-31T10:00:00",
      "caseId": null,
      "createdAt": "2025-10-31T10:00:00"
    }
  ],
  "total": 1
}
```

**Database Updates:**  
None - read-only query from `SentEmails` table.

**Example curl command:**
```bash
# Get all sent emails for a user
curl -X GET "http://localhost:8000/email/sent?user_id=test_user_123"

# Get all sent emails for a case
curl -X GET "http://localhost:8000/email/sent?case_id=case_789"

# Get all sent emails (no filter)
curl -X GET "http://localhost:8000/email/sent"
```

---

#### 11. Get Sent Email Detail
**Endpoint:** `GET /email/sent/{email_id}`

**What it does:**  
Retrieves detailed information about a sent email including all its replies.

**Input Parameters:**
- `email_id` (path, required): Sent email identifier (e.g., `sent_abc123def456`)

**Returns:**
```json
{
  "id": "sent_abc123def456",
  "userId": "test_user_123",
  "subject": "Test Email",
  "body": "<p>Email content</p>",
  "bodyType": "HTML",
  "toRecipients": [{"address": "...", "name": "..."}],
  "ccRecipients": null,
  "bccRecipients": null,
  "importance": "normal",
  "outlookMessageId": "AAMkADU...",
  "outlookConversationId": "AAQkADU...",
  "trackingId": "A1B2C3D4",
  "sentAt": "2025-10-31T10:00:00",
  "caseId": null,
  "createdAt": "2025-10-31T10:00:00",
  "replies": [
    {
      "id": "reply_xyz789",
      "sentEmailId": "sent_abc123def456",
      "outlookMessageId": "AAMkADU...",
      "fromAddress": {"address": "reply@example.com", "name": "Replier"},
      "subject": "Re: Test Email",
      "bodyPreview": "Thanks for your email...",
      "body": "<p>Full reply content</p>",
      "bodyType": "HTML",
      "receivedAt": "2025-10-31T11:00:00",
      "isRead": true,
      "hasAttachments": false,
      "importance": "normal",
      "createdAt": "2025-10-31T11:05:00",
      "updatedAt": "2025-10-31T11:05:00"
    }
  ]
}
```

**Database Updates:**  
None - read-only query from `SentEmails` and `EmailReplies` tables.

**Example curl command:**
```bash
curl -X GET "http://localhost:8000/email/sent/sent_abc123def456"
```

---

#### 12. Sync Email Replies
**Endpoint:** `POST /email/sent/{email_id}/sync-replies`

**What it does:**  
Syncs replies from Outlook for a specific sent email. Searches for replies using the conversation ID or tracking ID and saves them to the database.

**Input Parameters:**
- `email_id` (path, required): Sent email identifier

**Returns:**
```json
{
  "success": true,
  "message": "Successfully synced replies: 2 new, 1 updated",
  "newReplies": 2,
  "updatedReplies": 1
}
```

**Database Updates:**  
Inserts/updates rows in the `EmailReplies` table:
- `id`: Generated reply ID
- `sent_email_id`: Associated sent email ID
- `outlook_message_id`: Outlook message ID (unique)
- `from_address`: JSON with sender info
- `subject`: Reply subject
- `body_preview`: Preview of reply body
- `body`: Full reply body
- `body_type`: "HTML" or "Text"
- `received_at`: When reply was received
- `is_read`: Read status
- `has_attachments`: Whether reply has attachments
- `importance`: Reply importance
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Example curl command:**
```bash
curl -X POST "http://localhost:8000/email/sent/sent_abc123def456/sync-replies"
```

---

#### 13. Sync All Email Replies
**Endpoint:** `POST /email/sent/sync-all-replies`

**What it does:**  
Syncs replies from Outlook for all sent emails by a specific user. Processes each sent email and fetches new replies.

**Input Parameters:**
- `user_id` (query, required): User identifier

**Returns:**
```json
{
  "success": true,
  "message": "Successfully synced 5 email conversations: 8 new replies, 2 updated",
  "newReplies": 8,
  "updatedReplies": 2
}
```

**Database Updates:**  
Inserts/updates multiple rows in the `EmailReplies` table (same structure as "Sync Email Replies").

**Example curl command:**
```bash
curl -X POST "http://localhost:8000/email/sent/sync-all-replies?user_id=test_user_123"
```

---

#### 14. Get Inbox Messages (Debug)
**Endpoint:** `GET /email/inbox/messages`

**What it does:**  
Retrieves recent inbox messages for debugging reply detection. Can optionally filter by subject prefix.

**Input Parameters:**
- `user_id` (query, required): User identifier
- `top` (query, optional, default: 10, max: 50): Number of messages to return
- `filter_replies` (query, optional): Filter to only show messages starting with "Re: [filter_replies]"

**Returns:**
```json
{
  "emails": [
    {
      "id": "AAMkADU...",
      "subject": "Re: Test Email",
      "bodyPreview": "Thanks for...",
      "from_address": {"address": "...", "name": "..."},
      "toRecipients": [...],
      "ccRecipients": null,
      "receivedDateTime": "2025-10-31T10:00:00Z",
      "isRead": false,
      "hasAttachments": false,
      "importance": "normal"
    }
  ],
  "nextLink": null,
  "total": 1
}
```

**Database Updates:**  
None - read-only query to Microsoft Graph API.

**Example curl command:**
```bash
# Get 20 most recent inbox messages
curl -X GET "http://localhost:8000/email/inbox/messages?user_id=test_user_123&top=20"

# Filter for replies to a specific subject
curl -X GET "http://localhost:8000/email/inbox/messages?user_id=test_user_123&filter_replies=Test%20Email"
```

---

#### 15. Add Manual Reply
**Endpoint:** `POST /email/sent/{email_id}/add-reply`

**What it does:**  
Manually adds a reply to a sent email. Useful for testing or when automatic sync doesn't detect a reply.

**Input Parameters:**
- `email_id` (path, required): Sent email identifier
- **Request body (JSON):**
  ```json
  {
    "outlookMessageId": "AAMkADU...",
    "fromAddress": {
      "address": "replier@example.com",
      "name": "John Replier"
    },
    "subject": "Re: Test Email",
    "bodyPreview": "Thanks for your email...",
    "body": "<p>Full reply content</p>",
    "bodyType": "HTML",
    "receivedAt": "2025-10-31T11:00:00",
    "isRead": false,
    "hasAttachments": false,
    "importance": "normal"
  }
  ```

**Returns:**
```json
{
  "success": true,
  "message": "Reply added successfully",
  "newReplies": 1,
  "updatedReplies": 0
}
```

**Database Updates:**  
Inserts a row in the `EmailReplies` table:
- `id`: Generated reply ID
- `sent_email_id`: Associated sent email ID
- `outlook_message_id`: Outlook message ID from request
- `from_address`: Sender info from request
- `subject`: Reply subject from request
- `body_preview`: Preview from request
- `body`: Full body from request
- `body_type`: Body type from request
- `received_at`: Timestamp from request
- `is_read`: Read status from request
- `has_attachments`: Attachment status from request
- `importance`: Importance from request
- `created_at`: Current timestamp
- `updated_at`: Current timestamp

**Example curl command:**
```bash
curl -X POST "http://localhost:8000/email/sent/sent_abc123def456/add-reply" \
  -H "Content-Type: application/json" \
  -d '{
    "outlookMessageId": "AAMkADUyMzYxNjU...",
    "fromAddress": {
      "address": "replier@example.com",
      "name": "John Replier"
    },
    "subject": "Re: Test Email",
    "bodyPreview": "Thanks for your email",
    "body": "<p>Thanks for your email. I will review and get back to you.</p>",
    "bodyType": "HTML",
    "receivedAt": "2025-10-31T11:00:00",
    "isRead": false,
    "hasAttachments": false,
    "importance": "normal"
  }'
```

---

## Usage Example

### Complete Workflow

```bash
# 1. Get authorization URL
curl -X GET "http://localhost:8000/email/authorize?user_id=test_user_123"
# Returns: {"authUrl": "https://login.microsoftonline.com/...", "state": "test_user_123"}
# Visit the authUrl in a browser to authorize

# 2. Check token status (after authorization)
curl -X GET "http://localhost:8000/email/status?user_id=test_user_123"
# Returns: {"hasToken": true, "email": "user@example.com", "expiresAt": "..."}

# 3. Send an email
curl -X POST "http://localhost:8000/email/send?user_id=test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "to": [{"address": "recipient@example.com", "name": "John Doe"}],
    "subject": "Hello from WOO",
    "body": "<p>This is a test email</p>",
    "bodyType": "HTML"
  }'
# Returns: {"success": true, "message": "Email sent successfully", "messageId": "sent_..."}

# 4. Get sent emails
curl -X GET "http://localhost:8000/email/sent?user_id=test_user_123"
# Returns list of all sent emails with tracking IDs

# 5. Sync replies for a sent email
curl -X POST "http://localhost:8000/email/sent/sent_abc123def456/sync-replies"
# Returns: {"success": true, "message": "...", "newReplies": 2, "updatedReplies": 0}

# 6. Get email details with replies
curl -X GET "http://localhost:8000/email/sent/sent_abc123def456"
# Returns sent email with all replies included
```

---

## Database Tables

The email module uses three main database tables:

### 1. OAuthTokens
**Purpose:** Stores OAuth access and refresh tokens for email access.

**Columns:**
- `user_id` (TEXT, PRIMARY KEY): User identifier
- `access_token` (TEXT): OAuth access token for Microsoft Graph API
- `refresh_token` (TEXT): OAuth refresh token for renewing access
- `expires_at` (REAL): Token expiration timestamp
- `created_at` (TEXT): When token was created
- `updated_at` (TEXT): When token was last updated

**Modified by:**
- `POST /email/callback` - Insert/update token after OAuth authorization
- `DELETE /email/revoke` - Delete token when revoking access
- Token refresh (automatic) - Update token when expired

---

### 2. SentEmails
**Purpose:** Tracks all emails sent through the system for reply detection and case management.

**Columns:**
- `id` (TEXT, PRIMARY KEY): Generated sent email ID (e.g., `sent_abc123def456`)
- `user_id` (TEXT): User who sent the email
- `subject` (TEXT): Email subject (without tracking ID)
- `body` (TEXT): Email body content
- `body_type` (TEXT): "HTML" or "Text"
- `to_recipients` (TEXT): JSON array of recipients
- `cc_recipients` (TEXT): JSON array of CC recipients
- `bcc_recipients` (TEXT): JSON array of BCC recipients
- `importance` (TEXT): "low", "normal", or "high"
- `outlook_message_id` (TEXT): Outlook message ID (if available)
- `outlook_conversation_id` (TEXT): Outlook conversation ID for threading
- `tracking_id` (TEXT): 8-character tracking ID added to subject (e.g., `A1B2C3D4`)
- `sent_at` (TEXT): When email was sent
- `case_id` (TEXT): Optional link to a case
- `created_at` (TEXT): When record was created

**Modified by:**
- `POST /email/send` - Insert new sent email record
- `POST /email/send/woo` - Insert new sent email record with WOO template

---

### 3. EmailReplies
**Purpose:** Stores replies to sent emails for tracking conversations.

**Columns:**
- `id` (TEXT, PRIMARY KEY): Generated reply ID (e.g., `reply_xyz789`)
- `sent_email_id` (TEXT): References `SentEmails.id` - which email this is replying to
- `outlook_message_id` (TEXT, UNIQUE): Outlook message ID from the reply
- `from_address` (TEXT): JSON with sender info (`{"address": "...", "name": "..."}`)
- `subject` (TEXT): Reply subject
- `body_preview` (TEXT): Preview of reply body
- `body` (TEXT): Full reply body content
- `body_type` (TEXT): "HTML" or "Text"
- `received_at` (TEXT): When reply was received
- `is_read` (INTEGER): 0 or 1 - whether reply has been read
- `has_attachments` (INTEGER): 0 or 1 - whether reply has attachments
- `importance` (TEXT): "low", "normal", or "high"
- `created_at` (TEXT): When record was created
- `updated_at` (TEXT): When record was last updated

**Modified by:**
- `POST /email/sent/{email_id}/sync-replies` - Insert/update replies for a specific email
- `POST /email/sent/sync-all-replies` - Insert/update replies for all user emails
- `POST /email/sent/{email_id}/add-reply` - Manually insert a reply

---

## Security Considerations

### Production Deployment

1. **Token Storage**: Enhance database token storage security
   - Store tokens encrypted at rest
   - Associate tokens with authenticated user sessions
   - Implement proper token cleanup and rotation
   - Consider using a secure key management service

2. **HTTPS Only**: Always use HTTPS in production
   - Update `MICROSOFT_REDIRECT_URI` to use HTTPS
   - Configure Azure app registration with production URL

3. **Environment Variables**: Use proper secret management
   - Azure Key Vault
   - AWS Secrets Manager
   - Or similar secure storage

4. **User Validation**: Add authentication middleware
   - Verify user_id matches authenticated session
   - Implement proper authorization checks

5. **Rate Limiting**: Add rate limiting to prevent abuse
   - Limit API calls per user
   - Implement exponential backoff

6. **Error Handling**: Don't expose sensitive information in errors
   - Log detailed errors server-side
   - Return generic error messages to clients

## Troubleshooting

### Common Issues

**Error: "User not authenticated or token expired"**
- Solution: User needs to authorize again via `/email/authorize`

**Error: "OAuth authorization failed"**
- Check CLIENT_ID and CLIENT_SECRET are correct
- Verify redirect URI matches Azure app registration
- Ensure API permissions are granted

**Error: "Microsoft Graph API error: 403"**
- Check that required permissions are added in Azure
- Admin consent may be required for organization accounts

**Token refresh fails**
- Refresh tokens can expire after 90 days of inactivity
- User needs to re-authorize

## Development Notes

### Testing

For local development:
1. Use `http://localhost:8000` as the base URL
2. Set redirect URI to `http://localhost:8000/email/callback`
3. Test with personal Microsoft account first

### Microsoft Graph API Documentation

- [Graph API Overview](https://docs.microsoft.com/en-us/graph/overview)
- [Mail API Reference](https://docs.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)

## Future Enhancements

- [x] ~~Implement database token storage~~ (Implemented)
- [x] ~~Track sent emails in database~~ (Implemented)
- [x] ~~Reply detection and tracking~~ (Implemented)
- [ ] Encrypted token storage at rest
- [ ] Add attachment download support
- [ ] Support for calendar integration
- [ ] Advanced email search functionality
- [ ] Folder management (create, delete)
- [ ] Email draft management
- [ ] Webhook support for real-time email notifications
- [ ] Support for shared mailboxes
- [ ] Custom email templates
- [ ] Batch operations for bulk email handling

## License

This module is part of the WOO project.

