import logging
from config import EMAIL_ACCOUNT, EMAIL_PASSWORD, IMAP_SERVER
from email_handler import fetch_emails
from ticket_logger import log_ticket, close_ticket
from email_sender import send_reply
from classifier import classify_issue

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/system.log"),
            logging.StreamHandler()
        ]
    )
def process_email(email_data):
    """Process a single email and send a response."""
    try:
        # Extract email data
        sender = email_data.get("from", "").strip()
        subject = email_data.get("subject", "").strip()
        body = email_data.get("body", "").strip()

        logging.info(f"Processing email from {sender} | Subject: {subject}")

        if not sender:
            logging.warning("Missing sender email. Skipping.")
            return False

        # Set defaults for missing fields
        if not subject:
            subject = "No Subject"
        if not body:
            body = "No message content"

        try:
            # Try to send reply first
            issue_type = send_reply(sender, subject, body)
            if issue_type:
                logging.info(f"Reply sent to {sender} | Issue type: {issue_type}")
            else:
                logging.error(f"Failed to send reply to {sender}")
                return False

            # Log ticket after successful reply
            ticket_id = log_ticket(sender, subject, body, issue_type)
            if ticket_id:
                logging.info(f"Ticket logged: {sender} | {issue_type} | {subject}")
            else:
                logging.error(f"Failed to log ticket for {sender}")
                return False

            return True

        except Exception as e:
            logging.exception(f"Error processing email: {str(e)}")
            return False

    except Exception as e:
        logging.exception(f"Error extracting email data: {str(e)}")
        return False


def main():
    setup_logging()
    logging.info("Support system initialized.")

    try:
        # Fetch new emails
        emails = fetch_emails(IMAP_SERVER, EMAIL_ACCOUNT, EMAIL_PASSWORD)
        
        if emails is None:
            logging.error("fetch_emails() returned None. Check email_handler for return logic.")
            return 1
            
        if not emails:
            logging.info("No new emails to process.")
            return 0
            
        logging.info(f"fetch_emails() completed. {len(emails)} emails fetched.")
        
        # Process each email
        success_count = 0
        for email_data in emails:
            try:
                if process_email(email_data):
                    success_count += 1
            except Exception as e:
                logging.exception(f"Error processing email: {str(e)}")
                continue
                
        # Report results
        if success_count == len(emails):
            logging.info(f"Successfully processed all {len(emails)} emails.")
            return 0
        else:
            logging.warning(f"Processed {success_count} out of {len(emails)} emails successfully.")
            return 1
            
    except Exception as e:
        logging.exception(f"Fatal error in main pipeline: {e}")
        return 1

if __name__ == "__main__":
    main()
