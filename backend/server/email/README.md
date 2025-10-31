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

### Authentication

#### 1. Get Authorization URL
```http
GET /email/authorize?user_id=user_123
```

**Response:**
```json
{
  "authUrl": "https://login.microsoftonline.com/...",
  "state": "user_123"
}
```

**Usage**: Redirect user to `authUrl` to authorize email access.

#### 2. OAuth Callback (Automatic)
```http
GET /email/callback?code=...&state=user_123
```

This endpoint is called automatically by Microsoft after user authorization.

#### 3. Check Token Status
```http
GET /email/status?user_id=user_123
```

**Response:**
```json
{
  "hasToken": true,
  "email": "user@example.com",
  "expiresAt": "2025-10-31T12:00:00"
}
```

#### 4. Revoke Access
```http
DELETE /email/revoke?user_id=user_123
```

### Email Operations

#### 1. Send Email
```http
POST /email/send?user_id=user_123
Content-Type: application/json

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
  "importance": "normal"
}
```

**Optional fields:**
- `cc`: Array of email addresses
- `bcc`: Array of email addresses
- `attachments`: Array of attachment objects
- `bodyType`: "HTML" or "Text"
- `importance`: "low", "normal", or "high"

**Response:**
```json
{
  "success": true,
  "message": "Email sent successfully"
}
```

#### 2. Get Emails
```http
GET /email/messages?user_id=user_123&folder=inbox&top=10&skip=0
```

**Parameters:**
- `user_id` (required): User identifier
- `folder` (optional): Mail folder (default: "inbox")
  - Options: "inbox", "sentitems", "drafts", "deleteditems", "junkemail"
- `top` (optional): Number of emails to return (1-100, default: 10)
- `skip` (optional): Number of emails to skip (for pagination)
- `filter_query` (optional): OData filter (e.g., "isRead eq false")

**Response:**
```json
{
  "emails": [
    {
      "id": "message-id",
      "subject": "Email Subject",
      "bodyPreview": "Preview of email content...",
      "from_address": {
        "address": "sender@example.com",
        "name": "Sender Name"
      },
      "toRecipients": [...],
      "receivedDateTime": "2025-10-31T10:00:00Z",
      "isRead": false,
      "hasAttachments": false,
      "importance": "normal"
    }
  ],
  "total": 1
}
```

#### 3. Get Email Details
```http
GET /email/messages/{message_id}?user_id=user_123
```

**Response**: Returns full email including complete body content.

#### 4. Mark Email as Read/Unread
```http
POST /email/messages/{message_id}/read?user_id=user_123&is_read=true
```

**Parameters:**
- `is_read`: true to mark as read, false to mark as unread

## Usage Example

### Frontend Flow

```typescript
// 1. Get authorization URL
const response = await fetch('/email/authorize?user_id=user_123');
const { authUrl } = await response.json();

// 2. Redirect user to Microsoft login
window.location.href = authUrl;

// 3. User authorizes and is redirected back to callback
// (This is handled automatically by the backend)

// 4. Send an email
await fetch('/email/send?user_id=user_123', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    to: [{ address: 'recipient@example.com', name: 'John Doe' }],
    subject: 'Hello from WOO',
    body: '<p>This is a test email</p>',
    bodyType: 'HTML'
  })
});

// 5. Get unread emails
const emails = await fetch(
  '/email/messages?user_id=user_123&filter_query=isRead eq false'
);
```

## Security Considerations

### Production Deployment

1. **Token Storage**: Replace in-memory `token_store` with secure database storage
   - Store tokens encrypted
   - Associate tokens with user sessions
   - Implement proper token cleanup

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

- [ ] Implement database token storage
- [ ] Add attachment download support
- [ ] Support for calendar integration
- [ ] Email search functionality
- [ ] Folder management (create, delete)
- [ ] Email draft management
- [ ] Webhook support for real-time email notifications
- [ ] Support for shared mailboxes
- [ ] Email templates
- [ ] Batch operations

## License

This module is part of the WOO project.

