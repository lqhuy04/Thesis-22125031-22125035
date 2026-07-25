import httpx
from app.config import settings

RESEND_API_URL = "https://api.resend.com/emails"


async def _deliver_email(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    """
    Gửi email qua Resend HTTP API (HTTPS port 443).

    Lý do không dùng smtplib: Railway (và nhiều cloud khác) chặn outbound SMTP
    ports 25/465/587 -> socket connect tới smtp.gmail.com bị "Network is unreachable",
    khiến request signup treo (pending) và không gửi được email.

    Nếu RESEND_API_KEY không được cấu hình -> chạy development mode, chỉ in nội dung
    ra console (hữu ích khi chạy local).
    """
    if not settings.RESEND_API_KEY:
        if settings.DEBUG:
            print("\n" + "=" * 60)
            print("EMAIL (Development Mode - no RESEND_API_KEY configured)")
            print("=" * 60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(text_body)
            print("=" * 60 + "\n")
            return True
        raise RuntimeError("Email delivery is not configured")

    payload = {
        "from": settings.FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(RESEND_API_URL, json=payload, headers=headers)

        if response.status_code >= 400:
            print(f"Failed to send email via Resend: {response.status_code} {response.text}")
            raise Exception(f"Resend API error {response.status_code}: {response.text}")

        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise


async def send_reset_email(to_email: str, reset_token_or_otp: str):
    """
    Send password reset email with OTP or reset link.
    Detects whether input is OTP (6 digits) or reset token (UUID) and formats accordingly.
    """
    is_otp = len(reset_token_or_otp) == 6 and reset_token_or_otp.isdigit()
    
    if is_otp:
        # OTP-based flow
        subject = "Your Stockrium password reset code"
        otp = reset_token_or_otp
        
        # Plain text version
        text_body = f"""
Password Reset Code

You requested to reset your password for your Stockrium account. Use the code below to reset your password:

Code: {otp}

This code will expire in 10 minutes. Do not share this code with anyone.

If you didn't request this, please ignore this email and do not share the code. Your password will remain unchanged.

Best regards,
The Stockrium Team
https://stockrium.vn
"""

        # HTML version with OTP display
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
                    .otp-box {{ background-color: #dbeafe; border: 2px solid #1e40af; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; }}
                    .otp-code {{ font-size: 36px; font-weight: bold; color: #1e40af; letter-spacing: 4px; font-family: 'Courier New', monospace; }}
                    .otp-expiry {{ color: #dc2626; font-weight: bold; margin-top: 10px; }}
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
                        <h2>Password Reset Code</h2>
                        <p>You requested to reset your password for your Stockrium account. Use the code below:</p>
                        
                        <div class="otp-box">
                            <div class="otp-code">{otp}</div>
                            <div class="otp-expiry">⏱️ Valid for 10 minutes</div>
                        </div>
                        
                        <div class="warning">
                            <strong>🔒 Security Notice:</strong> Do not share this code with anyone. Stockrium staff will never ask for your code. If you didn't request this, please ignore this email. Your password will remain unchanged.
                        </div>
                        
                        <p style="font-size: 14px; color: #6b7280;">
                            <strong>Steps to reset your password:</strong><br>
                            1. Open the Stockrium app<br>
                            2. Go to Password Reset<br>
                            3. Enter this code: <strong>{otp}</strong><br>
                            4. Create your new password
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
    else:
        # Token-based flow (legacy)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token_or_otp}"
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
    
    return await _deliver_email(to_email, subject, text_body, html_body)


async def send_verification_email(to_email: str, verification_otp: str):
    """
    Send account verification email with OTP.
    In development mode (no SMTP configured), just prints the OTP.
    """
    subject = "Verify your Stockrium account"

    text_body = f"""
Welcome to Stockrium!

Thank you for registering. Use the OTP below to verify your email address:

OTP Code: {verification_otp}

This code will expire in 10 minutes.

If you did not create this account, please ignore this email.

Best regards,
The Stockrium Team
https://stockrium.vn
"""

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
                .otp-box {{ background-color: #dbeafe; border: 2px solid #1e40af; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; }}
                .otp-code {{ font-size: 36px; font-weight: bold; color: #1e40af; letter-spacing: 4px; font-family: 'Courier New', monospace; }}
                .otp-expiry {{ color: #dc2626; font-weight: bold; margin-top: 10px; }}
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
                    <h2>Verify your email</h2>
                    <p>Thank you for registering. Use the OTP below to verify your email address:</p>

                    <div class="otp-box">
                        <div class="otp-code">{verification_otp}</div>
                        <div class="otp-expiry">⏱️ Valid for 10 minutes</div>
                    </div>

                    <div class="warning">
                        <strong>🔒 Security Notice:</strong> Do not share this code with anyone. If you did not create this account, please ignore this email.
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

    return await _deliver_email(to_email, subject, text_body, html_body)
