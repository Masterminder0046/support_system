import imaplib
import email
import logging
from email.header import decode_header
from email.utils import parseaddr
from config import EMAIL_ACCOUNT, EMAIL_PASSWORD, IMAP_SERVER

logger = logging.getLogger(__name__)

def fetch_emails(imap_server, email_account, email_password):
    emails = []

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_account, email_password)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            logger.warning("IMAP search failed or no unseen emails.")
            return []

        for num in messages[0].split():
            try:
                _, msg_data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                # Decode subject
                raw_subject = decode_header(msg["Subject"])[0][0]
                subject = raw_subject.decode() if isinstance(raw_subject, bytes) else raw_subject
                subject = subject or "(No Subject)"

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
                body = body or "(No Content)"

                # Append structured email data
                emails.append({
                    "from": from_email,
                    "subject": subject,
                    "body": body
                })

                # Mark email as seen
                mail.store(num, '+FLAGS', '\\Seen')

            except Exception as e:
                logger.error(f"Failed to process email {num} | Error: {e}")

        mail.logout()
        logger.info(f"fetch_emails() completed. {len(emails)} emails fetched.")
        return emails

    except Exception as e:
        logger.critical(f"Failed to connect to email server | Error: {e}")
        return []
