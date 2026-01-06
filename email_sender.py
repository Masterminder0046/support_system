import smtplib
import logging
import time
from email.mime.text import MIMEText
from config import EMAIL_ACCOUNT, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT
from classifier import classify_issue
from reply_templates import TEMPLATES

logger = logging.getLogger(__name__)

def send_reply(to_email, subject, body):
    logger.info(f"Sending reply to: {to_email}")
    
    # Validate inputs
    if not all([to_email, subject, body]):
        logger.error("Missing required email parameters")
        return "error"
    
    # Validate configuration
    if not all([EMAIL_ACCOUNT, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        logger.error("Missing email configuration")
        return "error"
    
    try:
        # Classify the issue and get appropriate template
        issue_type = classify_issue(subject, body)
        reply_message = TEMPLATES.get(issue_type, TEMPLATES["general"])

        msg = MIMEText(reply_message, "plain", "utf-8")
        msg["Subject"] = f"Re: {subject.strip() if subject else 'Support Acknowledgment'}"
        msg["From"] = EMAIL_ACCOUNT
        msg["To"] = to_email
        msg["Bcc"] = EMAIL_ACCOUNT  # ✅ So you see it in your inbox

        logger.info("Attempting to send email...")
        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                logger.debug("Connected to SMTP server")
                server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
                logger.debug("Authentication successful")
                server.sendmail(EMAIL_ACCOUNT, [to_email, EMAIL_ACCOUNT], msg.as_string())
                logger.info(f"Email sent successfully to {to_email}")
                # Add a small delay to prevent rate limiting
                time.sleep(1)
                return issue_type
                
        except smtplib.SMTPAuthenticationError as auth_err:
            logger.error(f"Authentication failed: {auth_err}")
            return "error"
        except smtplib.SMTPException as smtp_err:
            logger.error(f"SMTP error: {smtp_err}")
            return "error"
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {str(e)}", exc_info=True)
            return "error"
            
    except Exception as e:
        logger.error(f"❌ Error preparing email: {str(e)}", exc_info=True)
        return "error"
