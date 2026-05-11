import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

async def send_reset_email(to_email: str, reset_token: str):
    """
    Send password reset email
    In development mode (no SMTP configured), just prints the link
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    # Check if SMTP is configured
    if not settings.SMTP_USER or settings.SMTP_USER == "":
        # Development mode - just print the link
        print("\n" + "="*60)
        print("PASSWORD RESET LINK (Development Mode)")
        print("="*60)
        print(f"Email: {to_email}")
        print(f"Reset Link: {reset_link}")
        print(f"Token: {reset_token}")
        print("="*60 + "\n")
        return True
    
    # Production mode - send actual email
    subject = "Reset your Stockrium password"
    
    # Plain text version
    text_body = f"""
Password Reset Request

You requested to reset your password for your Stockrium account. Click the link below to proceed:

{reset_link}

This link will expire in 30 minutes.

If you didn't request this, please ignore this email and do not click the link. Your password will remain unchanged.

Best regards,
The Stockrium Team
https://stockrium.vn
"""

    # HTML version with better formatting
    html_body = f'''
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e40af; color: white; padding: 20px; text-align: center; border-radius: 4px 4px 0 0; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
                .button {{ display: inline-block; background-color: #dc2626; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .button:hover {{ background-color: #b91c1c; }}
                .footer {{ background-color: #f3f4f6; padding: 20px; font-size: 12px; color: #6b7280; text-align: center; border-top: 1px solid #e5e7eb; }}
                .footer a {{ color: #1e40af; text-decoration: none; }}
                .warning {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Stockrium</h1>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>You requested to reset your password for your Stockrium account. Click the button below to proceed:</p>
                    
                    <center>
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </center>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; background-color: #e5e7eb; padding: 10px; border-radius: 4px; font-size: 12px;">
                        {reset_link}
                    </p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong> This link will expire in 30 minutes. If you didn't request this, please ignore this email and do not click the link. Your password will remain unchanged.
                    </div>
                </div>
                <div class="footer">
                    <p>© 2024 Stockrium. All rights reserved.</p>
                    <p>
                        <a href="https://stockrium.vn">Visit Website</a> | 
                        <a href="https://stockrium.vn/contact">Contact Support</a>
                    </p>
                </div>
            </div>
        </body>
    </html>
    '''
    
    message = MIMEMultipart("alternative")
    message["From"] = settings.FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    
    # Attach both plain text and HTML versions
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))
    
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise


async def send_verification_email(to_email: str, verification_token: str):
    """
    Send account verification email.
    In development mode (no SMTP configured), just prints the link.
    """
    verify_link = f"{settings.BACKEND_URL}/api/auth/verify-email?token={verification_token}"

    # Check if SMTP is configured
    if not settings.SMTP_USER or settings.SMTP_USER == "":
        # Development mode - just print the link
        print("\n" + "="*60)
        print("EMAIL VERIFICATION LINK (Development Mode)")
        print("="*60)
        print(f"Email: {to_email}")
        print(f"Verification Link: {verify_link}")
        print(f"Token: {verification_token}")
        print("="*60 + "\n")
        return True

    # Production mode - send actual email
    subject = "Verify your Stockrium account"
    
    # Plain text version
    text_body = f"""
Welcome to Stockrium!

Thank you for registering. Please verify your email address by clicking the link below:

{verify_link}

This link will expire in 24 hours.

If you did not create this account, please ignore this email and do not click the link.

Best regards,
The Stockrium Team
https://stockrium.vn
"""

    # HTML version with better formatting
    html_body = f'''
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e40af; color: white; padding: 20px; text-align: center; border-radius: 4px 4px 0 0; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
                .button {{ display: inline-block; background-color: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .button:hover {{ background-color: #1e3a8a; }}
                .footer {{ background-color: #f3f4f6; padding: 20px; font-size: 12px; color: #6b7280; text-align: center; border-top: 1px solid #e5e7eb; }}
                .footer a {{ color: #1e40af; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Stockrium</h1>
                </div>
                <div class="content">
                    <h2>Welcome to Stockrium!</h2>
                    <p>Thank you for registering. Please verify your email address to activate your account and start analyzing Vietnamese stocks.</p>
                    
                    <center>
                        <a href="{verify_link}" class="button">Verify Email</a>
                    </center>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; background-color: #e5e7eb; padding: 10px; border-radius: 4px; font-size: 12px;">
                        {verify_link}
                    </p>
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #6b7280;">
                        <strong>Note:</strong> This link will expire in 24 hours. If you did not create this account, please ignore this email.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2024 Stockrium. All rights reserved.</p>
                    <p>
                        <a href="https://stockrium.vn">Visit Website</a> | 
                        <a href="https://stockrium.vn/contact">Contact Support</a>
                    </p>
                </div>
            </div>
        </body>
    </html>
    '''

    message = MIMEMultipart("alternative")
    message["From"] = settings.FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    
    # Attach both plain text and HTML versions
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise