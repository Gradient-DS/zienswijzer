# Token Persistence Migration Guide

## Overview

The email integration has been upgraded to use **persistent token storage** in the SQLite database. Your OAuth tokens will now survive server restarts!

## What Changed

### Before
- Tokens were stored in memory (`token_store` dictionary)
- Tokens were lost every time the server restarted
- You had to re-authorize after every server restart

### After
- Tokens are stored in the SQLite database (`OAuthTokens` table)
- Tokens persist across server restarts
- Automatic token refresh when expired
- No need to re-authorize unless token is explicitly revoked

## Files Modified

1. **`backend/server/db/schema.sql`**
   - Added new `OAuthTokens` table to store OAuth tokens
   - Includes index on `expires_at` for efficient queries

2. **`backend/server/db/database.py`**
   - Added `get_oauth_token(user_id)` - Retrieve token from database
   - Added `save_oauth_token(user_id, access_token, refresh_token, expires_at)` - Save/update token
   - Added `delete_oauth_token(user_id)` - Delete token

3. **`backend/server/db/__init__.py`**
   - Exported new OAuth token functions

4. **`backend/server/email/email.py`**
   - Removed in-memory `token_store` dictionary
   - Updated all token operations to use database functions
   - Token refresh now updates database instead of memory

5. **Documentation**
   - Updated `backend/server/db/README.md` with OAuth token functions
   - Updated `backend/server/email/SUMMARY.md` to reflect persistent storage

## Database Schema

The new `OAuthTokens` table:

```sql
CREATE TABLE OAuthTokens (
    user_id TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Design Decision:** No foreign key constraint to `Users` table to allow the email module to work independently with any `user_id` string.

## Migration Steps

### Automatic Migration

The database table is created automatically when you restart your server:

```bash
# The table will be created on server startup via init_db()
python -m server.__main__
```

### Manual Migration (Optional)

If you want to apply the migration immediately without restarting:

```bash
cd backend
python -c "from server.db import init_db; init_db()"
```

## Testing the Migration

Run the included test to verify token persistence:

```bash
cd backend
python -c "
from server.db import save_oauth_token, get_oauth_token, delete_oauth_token
import time

# Save a token
save_oauth_token('test_user', 'access_123', 'refresh_456', time.time() + 3600)
print('✅ Token saved')

# Retrieve it
token = get_oauth_token('test_user')
print(f'✅ Token retrieved: {token[\"access_token\"][:10]}...')

# Delete it
delete_oauth_token('test_user')
print('✅ Token deleted')
"
```

## Backwards Compatibility

⚠️ **Important:** Any tokens stored in memory before this migration will be lost. Users will need to re-authorize their email access **one more time** after upgrading. After that, tokens will persist.

## How It Works

1. **First Authorization:**
   - User authorizes via `/email/authorize` endpoint
   - OAuth callback receives tokens
   - Tokens are saved to database with expiration time

2. **Using the Token:**
   - All email operations check database for valid token
   - If token exists and not expired, it's used immediately
   - If token is expired, it's automatically refreshed using refresh token

3. **Token Refresh:**
   - Happens automatically when access token expires
   - New tokens are saved back to database
   - User doesn't need to re-authorize

4. **Server Restart:**
   - Database persists on disk
   - Tokens are loaded from database when needed
   - No interruption to service

## API Changes

**No breaking changes!** The API endpoints remain exactly the same:

- `GET /email/authorize?user_id={id}` - Get authorization URL
- `GET /email/callback?code={code}&state={user_id}` - OAuth callback
- `GET /email/status?user_id={id}` - Check token status
- `POST /email/send?user_id={id}` - Send email
- `GET /email/messages?user_id={id}` - List emails
- `DELETE /email/revoke?user_id={id}` - Revoke access

## Benefits

✅ **Persistent Storage:** Tokens survive server restarts
✅ **Better UX:** Users don't need to re-authorize frequently
✅ **Automatic Refresh:** Tokens are refreshed transparently
✅ **Production Ready:** Database storage is more reliable than memory
✅ **Multi-User Support:** Each user's tokens stored independently
✅ **Easy Cleanup:** Simple delete operation to revoke access

## Security Considerations

### Current Implementation
- ✅ Tokens stored in database (persistent)
- ⚠️ Tokens stored in plaintext (readable by anyone with DB access)

### For Production
Consider adding:
- 🔒 Token encryption at rest using `cryptography` library
- 🔒 Database encryption using SQLCipher
- 🔒 Environment-based encryption keys
- 🔒 Token rotation policies
- 🔒 Audit logging for token access

## Troubleshooting

### Table Already Exists Error
If you get a "table already exists" error, the migration has already been applied. No action needed.

### Foreign Key Constraint Error
The `OAuthTokens` table intentionally has no foreign key constraint to the `Users` table. This allows the email module to work with any `user_id` string, even if the user doesn't exist in your `Users` table.

### Lost Tokens After Upgrade
This is expected. Users will need to re-authorize **once** after upgrading to the new persistent storage. After that, tokens will persist across restarts.

### Database Locked Error
Make sure only one process is accessing the database at a time. SQLite has limited concurrent write support.

## Example Usage

```python
from server.db import get_oauth_token, save_oauth_token, delete_oauth_token
import time

# Save a token (usually done by OAuth callback)
save_oauth_token(
    user_id="user_123",
    access_token="EwB4A+l3BAAUO9chh8c...",
    refresh_token="M.R3_BAY.-CXPYakXEI...",
    expires_at=time.time() + 3600  # 1 hour from now
)

# Get a token (usually done by email operations)
token = get_oauth_token("user_123")
if token:
    print(f"Access token: {token['access_token']}")
    print(f"Expires at: {token['expires_at']}")

# Delete a token (revoke access)
delete_oauth_token("user_123")
```

## Next Steps

1. ✅ Migration is complete - tokens are now persistent!
2. Test the integration by authorizing and restarting the server
3. Verify tokens persist after restart
4. (Optional) Add token encryption for production use
5. (Optional) Implement token rotation policies

## Questions?

Refer to:
- `backend/server/email/README.md` - Full email integration docs
- `backend/server/email/QUICKSTART.md` - Quick start guide
- `backend/server/db/README.md` - Database documentation

---

**Migration Date:** October 31, 2025
**Version:** 0.2.0
**Status:** ✅ Complete

