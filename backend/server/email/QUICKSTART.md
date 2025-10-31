# Quick Start Guide - Email Integration

This guide will help you quickly set up and test the Microsoft Outlook email integration.

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Azure App Registration

### Create App in Azure Portal

1. Go to https://portal.azure.com/
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Fill in:
   - **Name**: WOO Email Integration
   - **Account types**: Accounts in any organizational directory and personal Microsoft accounts
   - **Redirect URI**: Web → `http://localhost:8000/email/callback`
4. Click **Register**

### Configure Permissions

1. Go to **API permissions** → **Add a permission**
2. Select **Microsoft Graph** → **Delegated permissions**
3. Add these permissions:
   - `User.Read`
   - `Mail.Read`
   - `Mail.Send`
   - `Mail.ReadWrite`
4. Click **Grant admin consent for [your tenant]** (if available)

### Create Client Secret

1. Go to **Certificates & secrets** → **New client secret**
2. Add description (e.g., "WOO Email Integration Secret")
3. Set expiration (e.g., 6 months)
4. **Copy the Value immediately** (you can't see it again!)

### Get Your Credentials

- **Client ID**: On the Overview page (looks like: `12345678-1234-1234-1234-123456789abc`)
- **Client Secret**: The value you just copied
- **Tenant ID**: On the Overview page (optional, we use 'common' endpoint)

## Step 3: Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# backend/.env
MICROSOFT_CLIENT_ID=your-client-id-here
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_REDIRECT_URI=http://localhost:8000/email/callback
```

**Important**: Add `.env` to your `.gitignore` if not already there!

## Step 4: Integrate with FastAPI App

Add these lines to `backend/server/app.py`:

```python
# At the top with other imports
from server.email import email_router

# After creating the app and adding middleware
app.include_router(email_router)
```

Or see `integration_example.py` for a complete example.

## Step 5: Start the Server

```bash
cd backend
python -m server
# or
uvicorn server.app:app --reload --port 8000
```

## Step 6: Test the Integration

### Test 1: Get Authorization URL

Open your browser or use curl:

```bash
curl "http://localhost:8000/email/authorize?user_id=test_user_123"
```

Response:
```json
{
  "authUrl": "https://login.microsoftonline.com/...",
  "state": "test_user_123"
}
```

### Test 2: Authorize Email Access

1. Copy the `authUrl` from the response
2. Paste it in your browser
3. Sign in with your Microsoft account
4. Grant the requested permissions
5. You'll be redirected back to `http://localhost:8000/email/callback`
6. You should see a success response with your email

### Test 3: Check Token Status

```bash
curl "http://localhost:8000/email/status?user_id=test_user_123"
```

Response:
```json
{
  "hasToken": true,
  "email": "your-email@example.com",
  "expiresAt": "2025-10-31T12:00:00"
}
```

### Test 4: Read Emails

```bash
curl "http://localhost:8000/email/messages?user_id=test_user_123&folder=inbox&top=5"
```

This will return your 5 most recent inbox emails.

### Test 5: Send an Email

```bash
curl -X POST "http://localhost:8000/email/send?user_id=test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "to": [
      {
        "address": "lex@gradient-ds.com",
        "name": "Lex Lubbers"
      }
    ],
    "subject": "Test Email from WOO",
    "body": "<h1>Hello!</h1><p>This is a test email from the WOO email integration.</p>",
    "bodyType": "HTML"
  }'
```

**Note**: Send the email to yourself first to verify it works!

## Step 7: View API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Navigate to the "email" section to see all available endpoints and try them interactively.

## Common Test Scenarios

### Send Email to Yourself

```bash
curl -X POST "http://localhost:8000/email/send?user_id=test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "to": [{"address": "your-email@example.com"}],
    "subject": "Test from WOO",
    "body": "This is a test email",
    "bodyType": "Text"
  }'
```

### Get Unread Emails Only

```bash
curl "http://localhost:8000/email/messages?user_id=test_user_123&filter_query=isRead%20eq%20false"
```

### Get Email Details

```bash
# First, get a message ID from the list of emails
curl "http://localhost:8000/email/messages/MESSAGE_ID_HERE?user_id=test_user_123"
```

### Mark Email as Read

```bash
curl -X POST "http://localhost:8000/email/messages/MESSAGE_ID_HERE/read?user_id=test_user_123&is_read=true"
```

## Frontend Integration Example

```javascript
// 1. Start OAuth flow
async function authorizeEmail() {
  const userId = 'current_user_id';
  const response = await fetch(`/email/authorize?user_id=${userId}`);
  const { authUrl } = await response.json();
  
  // Redirect to Microsoft login
  window.location.href = authUrl;
}

// 2. After redirect, check status
async function checkEmailStatus() {
  const userId = 'current_user_id';
  const response = await fetch(`/email/status?user_id=${userId}`);
  const status = await response.json();
  
  if (status.hasToken) {
    console.log('Email connected:', status.email);
  } else {
    console.log('Need to authorize');
  }
}

// 3. Send an email
async function sendEmail() {
  const userId = 'current_user_id';
  const response = await fetch(`/email/send?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      to: [{ address: 'recipient@example.com', name: 'John Doe' }],
      subject: 'Hello from WOO',
      body: '<p>This is an HTML email</p>',
      bodyType: 'HTML'
    })
  });
  
  const result = await response.json();
  console.log('Email sent:', result);
}

// 4. Get recent emails
async function getEmails() {
  const userId = 'current_user_id';
  const response = await fetch(
    `/email/messages?user_id=${userId}&top=10&folder=inbox`
  );
  const { emails } = await response.json();
  
  emails.forEach(email => {
    console.log(`${email.subject} - from ${email.from_address.address}`);
  });
}
```

## Troubleshooting

### Error: "User not authenticated or token expired"

**Solution**: Run the authorization flow again:
```bash
curl "http://localhost:8000/email/authorize?user_id=test_user_123"
```

### Error: "OAuth authorization failed"

**Possible causes**:
- Client ID or secret is incorrect
- Redirect URI doesn't match Azure configuration
- Permissions not granted in Azure

**Solution**: 
1. Double-check your `.env` file
2. Verify redirect URI in Azure matches exactly
3. Ensure permissions are added and consented

### Error: "Microsoft Graph API error: 403"

**Solution**: Check that all required permissions are granted in Azure and admin consent is provided if required.

### No emails returned

**Possible causes**:
- No emails in the specified folder
- Filter query is too restrictive

**Solution**: Try without filters first:
```bash
curl "http://localhost:8000/email/messages?user_id=test_user_123&folder=inbox"
```

### Can't send emails

**Possible causes**:
- `Mail.Send` permission not granted
- Invalid recipient email address

**Solution**: 
1. Check permissions in Azure
2. Try sending to your own email first
3. Check request format matches the API

## Next Steps

1. **Production Setup**:
   - Use HTTPS for redirect URI
   - Store tokens in database (not in-memory)
   - Add proper authentication middleware
   - Enable rate limiting

2. **Enhanced Features**:
   - Add attachment support
   - Implement email templates
   - Add email search
   - Support for folders management

3. **Frontend Integration**:
   - Create OAuth flow UI
   - Build email compose component
   - Add email list view
   - Implement email reader

## Security Reminders

- ✅ Never commit `.env` file
- ✅ Use HTTPS in production
- ✅ Store tokens securely (database, encrypted)
- ✅ Validate user permissions before operations
- ✅ Implement rate limiting
- ✅ Rotate client secrets regularly

## Support

For issues or questions:
- Check the [Microsoft Graph API docs](https://docs.microsoft.com/en-us/graph/)
- Review the [MSAL Python documentation](https://msal-python.readthedocs.io/)
- See `README.md` for detailed documentation

## Testing Checklist

- [ ] Azure app registered
- [ ] Permissions configured and consented
- [ ] Client secret created and saved
- [ ] Environment variables set
- [ ] Dependencies installed
- [ ] Email router integrated
- [ ] Server running
- [ ] Authorization flow completed
- [ ] Token status verified
- [ ] Can read emails
- [ ] Can send emails
- [ ] Can mark emails as read

Once all items are checked, your email integration is ready! 🎉

