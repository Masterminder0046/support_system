import os
from dotenv import load_dotenv

# Load .env from the current directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# ✅ Email Credentials
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# ✅ IMAP (Receiving)
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
IMAP_TIMEOUT = int(os.getenv("IMAP_TIMEOUT", 30))

# ✅ SMTP (Sending)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
USE_SSL = os.getenv("USE_SSL", "False").lower() == "true"

# ✅ Retry Logic
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))

# ✅ Validation
REQUIRED_EMAIL_VARS = {
    "EMAIL_ACCOUNT": EMAIL_ACCOUNT,
    "EMAIL_PASSWORD": EMAIL_PASSWORD,
    "IMAP_SERVER": IMAP_SERVER,
    "SMTP_SERVER": SMTP_SERVER
}

missing = [key for key, value in REQUIRED_EMAIL_VARS.items() if not value]
if missing:
    raise EnvironmentError(f"Missing required email config variables: {', '.join(missing)}")
