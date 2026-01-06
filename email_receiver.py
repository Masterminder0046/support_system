import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr

from config import EMAIL_ACCOUNT, EMAIL_PASSWORD, IMAP_SERVER
from email_sender import send_reply
from ticket_logger import log_ticket

def receive_email(from_email, subject, body):
    print(f"📨 Processing email from {from_email} | Subject: {subject}")
    try:
        issue_type = send_reply(from_email, subject, body)
        print(f"✅ Reply sent to {from_email} | Issue type: {issue_type}")
        log_ticket(from_email, subject, body, issue_type)
    except Exception as e:
        print(f"❌ Failed to send reply to {from_email}: {e}")


def fetch_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        print("✅ IMAP login successful")
    except Exception as e:
        print(f"❌ IMAP login failed: {e}")
        return

    mail.select("inbox")
    status, messages = mail.search(None, "UNSEEN")
    if status != "OK":
        print("❌ Failed to search inbox")
        return

    for num in messages[0].split():
        _, msg_data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        # Decode subject
        subject = decode_header(msg["Subject"])[0][0]
        subject = subject.decode() if isinstance(subject, bytes) else subject

        # Extract sender
        from_email = parseaddr(msg.get("From"))[1]

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and not part.get("Content-Disposition"):
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        receive_email(from_email, subject, body)

    mail.logout()
    print("📬 All emails processed.")

if __name__ == "__main__":
    fetch_emails()
