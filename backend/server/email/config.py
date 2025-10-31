"""
Email module configuration using Pydantic.

This module provides configuration management for the Microsoft Outlook
email integration using Pydantic Settings for type-safe environment variables.

Configuration is loaded from backend/.env file. To set up:
    1. Copy backend/.env.example to backend/.env
    2. Update the values with your Azure AD app registration credentials

Usage:
    from .config import email_config
    
    # Access configuration values
    client_id = email_config.client_id
    scopes = email_config.scopes
    
Environment Variables (all prefixed with MICROSOFT_):
    MICROSOFT_CLIENT_ID: OAuth client ID from Azure AD app registration (required)
    MICROSOFT_CLIENT_SECRET: OAuth client secret from Azure AD app registration (required)
    MICROSOFT_TENANT_ID: Azure AD tenant ID (required) - enables single-tenant authentication
    MICROSOFT_REDIRECT_URI: OAuth callback URL (default: http://localhost:8000/email/callback)
    MICROSOFT_GRAPH_API_ENDPOINT: Graph API endpoint (default: https://graph.microsoft.com/v1.0)
    MICROSOFT_SCOPES: Comma-separated OAuth scopes (default: User.Read,Mail.Read,Mail.Send,Mail.ReadWrite)
    MICROSOFT_MAX_EMAILS_PER_REQUEST: Maximum emails per request (default: 100)
    MICROSOFT_DEFAULT_EMAILS_PER_PAGE: Default page size (default: 10)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union, Optional
from pathlib import Path
from pydantic import field_validator


class EmailConfig(BaseSettings):
    """
    Email integration configuration.
    
    All settings can be configured via environment variables with the prefix
    MICROSOFT_ (e.g., MICROSOFT_CLIENT_ID).
    """
    
    model_config = SettingsConfigDict(
        env_prefix="MICROSOFT_",
        case_sensitive=False,
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Microsoft OAuth credentials (required - no defaults for security)
    client_id: str
    client_secret: str
    tenant_id: str
    
    # Microsoft OAuth configuration
    redirect_uri: str = "http://localhost:8000/email/callback"
    
    # Microsoft Graph API configuration
    graph_api_endpoint: str = "https://graph.microsoft.com/v1.0"
    authority: Optional[str] = None  # Will be built from tenant_id
    
    # OAuth scopes required for email operations
    scopes: Union[str, List[str]] = [
        "User.Read",
        "Mail.Read",
        "Mail.Send",
        "Mail.ReadWrite"
    ]
    
    # Email query limits
    max_emails_per_request: int = 100
    default_emails_per_page: int = 10

    @field_validator('scopes', mode='after')
    @classmethod
    def parse_scopes(cls, v):
        """Parse comma-separated scopes string into a list"""
        if isinstance(v, str):
            return [scope.strip() for scope in v.split(',') if scope.strip()]
        return v

    def __init__(self, **data):
        super().__init__(**data)
        # Build tenant-specific authority URL
        if not self.authority:
            self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"


# Global config instance
email_config = EmailConfig()


__all__ = ["email_config", "EmailConfig"]

