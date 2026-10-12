from redmail.email import gmail
from app.core.config import settings
import textwrap
from smtplib import SMTPException
import logging

logger = logging.getLogger(__name__)

def send_password_reset_link(email: str, reset_url: str):
    gmail.username = settings.GMAIL
    gmail.password = settings.APP_PASSWORD

    email_subject = "Reset your password"
    email_body = textwrap.dedent(f"""\
        Hi,

        We received a request to reset the password for your account. If you made this request, click the button below to choose a new password:

        [ Reset Your Password ] (Link: {reset_url})

        Note: This password reset link is secure and will expire in 30 minutes.

        If you didn’t request a password reset, you can safely ignore this email—your password will remain unchanged.

        Best regards,

        The Team
""")
    try:
        gmail.send(
            subject=email_subject,
            receivers=[email],
            text=email_body
        )
    except SMTPException as e:
        logger.exception(f"Failed to send email: {e}")
        raise