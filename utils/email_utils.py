import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import Config


def send_email_otp(to_email: str, otp: str, purpose: str = "verify your account") -> bool:
    """
    Sends a real OTP email using SMTP (Gmail by default).
    Returns True on success, False on failure (failure is logged, not raised,
    so the caller can decide how to respond to the user).
    """
    if not Config.EMAIL_ENABLED:
        print(f"[EMAIL DISABLED] Would send OTP {otp} to {to_email}")
        return False

    subject = "Your verification code"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2 style="color:#1877f2;">Verification Code</h2>
        <p>Use the code below to {purpose}. This code expires in
        {Config.OTP_EXPIRY_MINUTES} minutes.</p>
        <div style="font-size: 32px; font-weight: bold; letter-spacing: 6px;
                    background:#f0f2f5; padding: 16px 24px; border-radius: 8px;
                    text-align:center; color:#1c1e21;">
            {otp}
        </div>
        <p style="color:#65676b; font-size: 13px; margin-top: 20px;">
        If you didn't request this code, you can safely ignore this email.
        </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{Config.SMTP_SENDER_NAME} <{Config.SMTP_USERNAME}>"
    msg["To"] = to_email
    msg.attach(MIMEText(f"Your verification code is {otp}", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_USERNAME, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
