#!/usr/bin/env python
"""
Test script to verify email configuration and OTP sending.
Run this with: python test_email.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicart.settings')
django.setup()

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from users.otp_service import generate_otp, send_otp_email

print("=" * 60)
print("MEDICART EMAIL CONFIGURATION TEST")
print("=" * 60)

# Display current settings
print("\n📧 Email Backend Configuration:")
print(f"  Backend: {settings.EMAIL_BACKEND}")
print(f"  Host: {settings.EMAIL_HOST}")
print(f"  Port: {settings.EMAIL_PORT}")
print(f"  Use TLS: {settings.EMAIL_USE_TLS}")
print(f"  From Email: {settings.DEFAULT_FROM_EMAIL}")
print(f"  Host User: {settings.EMAIL_HOST_USER}")
print(f"  Host Password: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else '(not set)'}")

# Test 1: Send a simple test email
print("\n" + "-" * 60)
print("TEST 1: Sending a simple test email...")
print("-" * 60)

try:
    test_email = input("Enter your email address to test: ").strip()
    if not test_email:
        print("❌ No email provided. Skipping test 1.")
    else:
        result = send_mail(
            subject="MediCart - Email Test",
            message="This is a test email from MediCart. If you received this, email configuration is working!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        if result == 1:
            print(f"✅ Test email sent successfully to {test_email}")
        else:
            print(f"❌ Failed to send test email")
except Exception as e:
    print(f"❌ Error sending test email: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Send OTP email
print("\n" + "-" * 60)
print("TEST 2: Testing OTP Email Sending...")
print("-" * 60)

try:
    otp_email = input("Enter email for OTP test (can be same as above): ").strip()
    if not otp_email:
        print("❌ No email provided. Skipping test 2.")
    else:
        test_otp = generate_otp()
        print(f"Generated OTP: {test_otp}")
        
        success, error = send_otp_email(otp_email, test_otp, purpose='registration')
        
        if success:
            print(f"✅ OTP email sent successfully to {otp_email}")
            print(f"📬 Check your inbox for the OTP verification email")
        else:
            print(f"❌ Failed to send OTP email: {error}")
except Exception as e:
    print(f"❌ Error in OTP test: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Configuration validation
print("\n" + "-" * 60)
print("TEST 3: Configuration Validation")
print("-" * 60)

checks = []

# Check backend
if "smtp" in settings.EMAIL_BACKEND.lower():
    checks.append(("✅", "Email backend set to SMTP", True))
else:
    checks.append(("❌", "Email backend NOT set to SMTP (currently: console)", False))

# Check host
if settings.EMAIL_HOST:
    checks.append(("✅", f"Email host configured: {settings.EMAIL_HOST}", True))
else:
    checks.append(("❌", "Email host not configured", False))

# Check credentials
if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
    checks.append(("✅", "Email credentials configured", True))
else:
    checks.append(("❌", "Email credentials missing (HOST_USER or HOST_PASSWORD)", False))

# Check FROM email
if settings.DEFAULT_FROM_EMAIL:
    checks.append(("✅", f"Default FROM email set: {settings.DEFAULT_FROM_EMAIL}", True))
else:
    checks.append(("❌", "Default FROM email not set", False))

for status, message, passed in checks:
    print(f"{status} {message}")

all_passed = all(check[2] for check in checks)

print("\n" + "=" * 60)
if all_passed:
    print("✅ All checks passed! Email should work correctly.")
else:
    print("❌ Some checks failed. Review the .env file configuration.")
print("=" * 60)
