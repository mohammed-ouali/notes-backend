import asyncio
import smtplib
from email.message import EmailMessage
from app.core.config import settings

class EmailService:
    async def send_welcome_email(self, to_email: str) -> None:
        await asyncio.to_thread(self._send_welcome_email, to_email)

    def _send_welcome_email(self, to_email: str) -> None:
        message = EmailMessage()

        message["Subject"] = "Welcome to notes app"
        message["From"] = settings.smtp_from
        message["To"] = to_email

        message.set_content(f"Welcome to notes app, the place that holds your secrets\nFor anny support contact: {settings.smtp_from}")

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
