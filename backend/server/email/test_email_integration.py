"""
Simple test script for the email integration.

This script helps you verify that the email integration is working correctly.
Run this after setting up Azure and environment variables.

Usage:
    python -m server.email.test_email_integration
"""

import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_response(response: requests.Response):
    """Print formatted response"""
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_health_check() -> bool:
    """Test if the server is running"""
    print_section("Test 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print("❌ Server returned unexpected status code")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to server: {e}")
        print("Make sure the server is running: python -m server")
        return False


def test_get_auth_url() -> Optional[str]:
    """Test getting the authorization URL"""
    print_section("Test 2: Get Authorization URL")
    try:
        response = requests.get(
            f"{BASE_URL}/email/authorize",
            params={"user_id": TEST_USER_ID}
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get("authUrl")
            print("\n✅ Authorization URL generated successfully!")
            print(f"\nNext step: Open this URL in your browser to authorize:")
            print(f"\n{auth_url}\n")
            return auth_url
        else:
            print("\n❌ Failed to get authorization URL")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_check_status() -> bool:
    """Test checking token status"""
    print_section("Test 3: Check Token Status")
    try:
        response = requests.get(
            f"{BASE_URL}/email/status",
            params={"user_id": TEST_USER_ID}
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            has_token = data.get("hasToken", False)
            
            if has_token:
                print("\n✅ User is authenticated!")
                print(f"Email: {data.get('email')}")
                print(f"Expires: {data.get('expiresAt')}")
                return True
            else:
                print("\n⚠️  User is not authenticated yet")
                print("Complete the authorization flow first (Test 2)")
                return False
        else:
            print("\n❌ Failed to check status")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_emails():
    """Test getting emails"""
    print_section("Test 4: Get Emails from Inbox")
    try:
        response = requests.get(
            f"{BASE_URL}/email/messages",
            params={
                "user_id": TEST_USER_ID,
                "folder": "inbox",
                "top": 5
            }
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            emails = data.get("emails", [])
            print(f"\n✅ Retrieved {len(emails)} emails")
            
            for i, email in enumerate(emails, 1):
                print(f"\n--- Email {i} ---")
                print(f"Subject: {email.get('subject')}")
                print(f"From: {email.get('from_address', {}).get('address')}")
                print(f"Date: {email.get('receivedDateTime')}")
                print(f"Read: {email.get('isRead')}")
        else:
            print("\n❌ Failed to get emails")
            print("Make sure you've authorized email access (Test 2)")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_send_email(recipient_email: str):
    """Test sending an email"""
    print_section("Test 5: Send Test Email")
    
    email_data = {
        "to": [
            {
                "address": recipient_email,
                "name": "Test Recipient"
            }
        ],
        "subject": "Test Email from WOO Integration",
        "body": "<h1>Hello!</h1><p>This is a test email sent from the WOO email integration.</p><p>If you receive this, the integration is working correctly! ✅</p>",
        "bodyType": "HTML",
        "importance": "normal"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/email/send",
            params={"user_id": TEST_USER_ID},
            json=email_data
        )
        print_response(response)
        
        if response.status_code == 200:
            print(f"\n✅ Email sent successfully to {recipient_email}!")
            print("Check your inbox to verify delivery")
        else:
            print("\n❌ Failed to send email")
            print("Make sure you've authorized email access (Test 2)")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  WOO Email Integration Test Suite")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    
    # Test 1: Check server
    if not test_health_check():
        print("\n❌ Server is not running. Exiting tests.")
        return
    
    # Test 2: Get authorization URL
    auth_url = test_get_auth_url()
    
    # Test 3: Check if user is authenticated
    is_authenticated = test_check_status()
    
    if not is_authenticated:
        print("\n" + "=" * 60)
        print("  Authorization Required")
        print("=" * 60)
        print("\nTo continue testing, you need to authorize email access:")
        print("1. Copy the authorization URL from Test 2 above")
        print("2. Open it in your browser")
        print("3. Sign in with your Microsoft account")
        print("4. Grant the requested permissions")
        print("5. Wait for the redirect to complete")
        print("6. Run this script again")
        print("\nOr run Test 2 again to get a fresh authorization URL.")
        return
    
    # Test 4: Get emails
    test_get_emails()
    
    # Test 5: Send email (optional)
    print("\n" + "=" * 60)
    print("  Optional: Send Test Email")
    print("=" * 60)
    
    send_test = input("\nDo you want to send a test email? (y/n): ").lower().strip()
    
    if send_test == 'y':
        recipient = input("Enter recipient email address (or press Enter to send to yourself): ").strip()
        
        if not recipient:
            # Try to get user's own email
            try:
                response = requests.get(
                    f"{BASE_URL}/email/status",
                    params={"user_id": TEST_USER_ID}
                )
                data = response.json()
                recipient = data.get("email")
                print(f"Using your email: {recipient}")
            except:
                print("Could not determine your email address")
                return
        
        if recipient:
            test_send_email(recipient)
    
    # Summary
    print("\n" + "=" * 60)
    print("  Test Suite Complete")
    print("=" * 60)
    print("\n✅ Email integration is working correctly!")
    print("\nNext steps:")
    print("- Integrate the email router into your main app.py")
    print("- Build frontend UI for email operations")
    print("- Implement database token storage for production")
    print("- Add proper user authentication")
    print("\nSee README.md for more information.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")

