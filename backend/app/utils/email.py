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
    subject = "Password Reset Request"
    body = f'''
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Click the link below to proceed:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>This link will expire in 30 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
    </html>
    '''
    
    message = MIMEMultipart()
    message["From"] = settings.FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))
    
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise