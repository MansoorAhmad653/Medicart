import secrets
import hashlib
import time
import resend
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Resend API
resend.api_key = os.getenv('RESEND_API_KEY', '')

# OTP Settings
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 600  # 10 minutes


def generate_otp():
    """Generate a secure 6-digit OTP code."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])


def _hash_otp(otp):
    """Hash an OTP for secure session storage."""
    return hashlib.sha256(otp.encode()).hexdigest()


def store_otp_in_session(request, email, otp, purpose='registration'):
    """
    Store OTP hash and expiry in Django session.
    purpose: 'registration' or 'password_reset'
    """
    request.session[f'otp_{purpose}_hash'] = _hash_otp(otp)
    request.session[f'otp_{purpose}_email'] = email
    request.session[f'otp_{purpose}_expiry'] = time.time() + OTP_EXPIRY_SECONDS
    request.session.modified = True


def verify_otp_from_session(request, email, otp, purpose='registration'):
    """
    Verify OTP against session-stored hash.
    Returns (success: bool, error_message: str or None)
    """
    stored_hash = request.session.get(f'otp_{purpose}_hash')
    stored_email = request.session.get(f'otp_{purpose}_email')
    expiry = request.session.get(f'otp_{purpose}_expiry')

    if not stored_hash or not stored_email or not expiry:
        return False, 'No OTP session found. Please request a new code.'

    if stored_email != email:
        return False, 'Email mismatch. Please request a new code.'

    if time.time() > expiry:
        # Clean up expired OTP
        clear_otp_session(request, purpose)
        return False, 'OTP has expired. Please request a new code.'

    if _hash_otp(otp) != stored_hash:
        return False, 'Invalid OTP. Please check and try again.'

    # OTP is valid — clean up
    clear_otp_session(request, purpose)
    return True, None


def clear_otp_session(request, purpose='registration'):
    """Remove OTP data from session."""
    for key in [f'otp_{purpose}_hash', f'otp_{purpose}_email', f'otp_{purpose}_expiry']:
        request.session.pop(key, None)
    request.session.modified = True


def send_otp_email(email, otp, purpose='registration'):
    """
    Send OTP email via Resend API.
    purpose: 'registration' or 'password_reset'
    Returns (success: bool, error_message: str or None)
    """
    if purpose == 'registration':
        subject = 'MediCart — Verify Your Email Address'
        heading = 'Email Verification'
        message = 'Thank you for signing up with MediCart! Use the code below to verify your email address.'
        icon = '🔐'
    else:
        subject = 'MediCart — Password Reset Code'
        heading = 'Password Reset'
        message = 'We received a request to reset your password. Use the code below to proceed.'
        icon = '🔑'

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background-color:#f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f4f6f9; padding:40px 20px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="480" cellspacing="0" cellpadding="0" style="background-color:#ffffff; border-radius:16px; box-shadow:0 4px 24px rgba(0,0,0,0.08); overflow:hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); padding:32px 40px; text-align:center;">
                                <div style="font-size:28px; margin-bottom:8px;">{icon}</div>
                                <h1 style="color:#ffffff; font-size:22px; margin:0; font-weight:600;">{heading}</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding:36px 40px 20px;">
                                <p style="color:#555; font-size:15px; line-height:1.6; margin:0 0 24px;">
                                    {message}
                                </p>
                                <!-- OTP Code -->
                                <div style="text-align:center; margin:24px 0;">
                                    <div style="display:inline-block; background:linear-gradient(135deg,#667eea10,#764ba210); border:2px dashed #667eea; border-radius:12px; padding:16px 36px;">
                                        <span style="font-size:36px; font-weight:800; letter-spacing:10px; color:#667eea; font-family:monospace;">
                                            {otp}
                                        </span>
                                    </div>
                                </div>
                                <p style="color:#999; font-size:13px; text-align:center; margin:16px 0 0;">
                                    This code expires in <strong>10 minutes</strong>.
                                </p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding:20px 40px 32px;">
                                <hr style="border:none; border-top:1px solid #eee; margin:0 0 20px;">
                                <p style="color:#bbb; font-size:12px; text-align:center; margin:0;">
                                    If you didn't request this code, you can safely ignore this email.
                                </p>
                                <p style="color:#bbb; font-size:12px; text-align:center; margin:8px 0 0;">
                                    &copy; 2024 MediCart — Your Health Partner
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    try:
        params = {
            "from": "MediCart <onboarding@resend.dev>",
            "to": [email],
            "subject": subject,
            "html": html_body,
        }
        response = resend.Emails.send(params)
        print(f"OTP email sent to {email}, Resend ID: {response.get('id', 'N/A')}")
        return True, None
    except Exception as e:
        print(f"Resend email error: {e}")
        return False, str(e)
