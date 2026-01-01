import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_reminder_email(recipient_email, subject, body_sinhala):
    """Sends a strategic reminder email to the user."""
    msg = MIMEMultipart()
    msg['From'] = os.getenv("EMAIL_USER")
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Using HTML to ensure the Sinhala text renders correctly in modern email clients
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
        server = smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT")))
        server.starttls() # Secure the connection
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False