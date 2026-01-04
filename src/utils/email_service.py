import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_reminder_email(recipient_email, subject, body_sinhala):
    """Sends a strategic reminder email to the user using SSL (Port 465)."""
    msg = MIMEMultipart()
    msg['From'] = os.getenv("EMAIL_USER")
    msg['To'] = recipient_email
    msg['Subject'] = subject

    html = f"""
    <html>
      <body style="font-family: sans-serif;">
        <h2 style="color: #2c3e50;">Sath-Chakra AI: ඔබගේ 2026 ප්‍රගතිය සමාලෝචනය කරන්න</h2>
        <p style="font-size: 16px;">{body_sinhala}</p>
        <hr>
        <p style="font-size: 12px; color: #7f8c8d;">මෙය Sath-Chakra AI වෙතින් ස්වයංක්‍රීයව එවනු ලබන පණිවිඩයකි.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    try:
        # Use SMTP_SSL for Port 465
        # This removes the need for server.starttls()
        server = smtplib.SMTP_SSL(
            os.getenv("EMAIL_HOST"),
            int(os.getenv("EMAIL_PORT"))
        )
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)
        server.quit()
        print(f"DEBUG: Email successfully sent to {recipient_email}")
        return True
    except Exception as e:
        # This will now catch and print errors more effectively for Railway logs
        print(f"DEBUG: Email FAILED to {recipient_email}. Error: {e}")
        return False