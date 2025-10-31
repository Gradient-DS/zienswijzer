"""
Example: How to integrate the email router with your main FastAPI app.

This file shows how to add the email endpoints to app.py.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the email router
from .email import email_router

# Your existing app setup
app = FastAPI(title="WOO Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the email router - this adds all /email/* endpoints
app.include_router(email_router)

# Your existing routes continue below...
# @app.get("/health")
# def health_check():
#     return {"status": "ok"}
# etc.


"""
Integration Steps for app.py:

1. Add import at the top of app.py:
   from server.email import email_router

2. After creating the app and adding middleware, include the router:
   app.include_router(email_router)

3. Set environment variables:
   MICROSOFT_CLIENT_ID=your-client-id
   MICROSOFT_CLIENT_SECRET=your-client-secret
   MICROSOFT_REDIRECT_URI=http://localhost:8000/email/callback

4. Install dependencies:
   pip install msal requests

5. Available endpoints:
   - GET  /email/authorize           - Get OAuth URL
   - GET  /email/callback            - OAuth callback (automatic)
   - GET  /email/status              - Check token status
   - POST /email/send                - Send an email
   - GET  /email/messages            - List emails
   - GET  /email/messages/{id}       - Get email details
   - POST /email/messages/{id}/read  - Mark as read/unread
   - DELETE /email/revoke            - Revoke access

All endpoints require a user_id query parameter (except callback).
"""

