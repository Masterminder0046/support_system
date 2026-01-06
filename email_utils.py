import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.utils import parseaddr
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from ticket_logger import get_db_connection, log_admin_reply
import logging

def send_email(to, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to, msg.as_string())

        logging.info(f"✅ Email sent to {to}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")
        return False

def normalize_subject(subject):
    prefixes = ["re:", "fwd:"]
    s = subject.lower() if subject else ""
    while True:
        for prefix in prefixes:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        else:
            break
    return s.strip()

def fetch_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(SMTP_USER, SMTP_PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, "UNSEEN")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        for num in messages[0].split():
            status, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            raw_subject = msg["subject"] or "No Subject"
            normalized_subject = normalize_subject(raw_subject)
            sender = parseaddr(msg["from"])[1]

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            logging.info(f"🔍 Checking for existing open ticket: email={sender}, normalized_subject={normalized_subject}")

            cursor.execute("""
                SELECT id FROM tickets
                WHERE email = %s AND subject = %s AND status != 'closed'
                ORDER BY id DESC LIMIT 1
            """, (sender, normalized_subject))
            existing = cursor.fetchone()

            if existing:
                ticket_id = existing["id"]
                log_admin_reply(ticket_id, body)
                logging.info(f"📨 Reply logged for ticket {ticket_id}")
            else:
                cursor.execute("""
                    INSERT INTO tickets (email, subject, raw_subject, message, issue_type, ack_sent, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (sender, normalized_subject, raw_subject, body, "general", 1, "open"))
                conn.commit()
                send_email(sender, f"Re: {raw_subject}", "Thank you for contacting support. We've created a ticket.")
                logging.info(f"🆕 New ticket created for {sender} | Subject: {raw_subject}")

        conn.close()
        mail.logout()
        logging.info("✅ Emails fetched and tickets updated.")
    except Exception as e:
        logging.error(f"❌ Failed to fetch emails: {e}")
