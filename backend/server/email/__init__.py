"""
Email integration module for Microsoft Outlook.

This module provides OAuth authentication and email operations
using the Microsoft Graph API.
"""

from .email import email_router

__all__ = ["email_router"]

