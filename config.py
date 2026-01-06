import os
from dotenv import load_dotenv

# 📦 Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# 🔐 Security
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")

# 📧 Email Configuration
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
IMAP_TIMEOUT = int(os.getenv("IMAP_TIMEOUT", 30))

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = EMAIL_ACCOUNT
SMTP_PASSWORD = EMAIL_PASSWORD  # Use Gmail App Password if 2FA is enabled

# 🗄️ Database Configuration (MySQL)
DB_HOST = os.getenv("DB_HOST", "::1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "customer_support")

# 📝 Logging Configuration
LOG_FILE = os.getenv("LOG_FILE", "logs/supportsync.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

# 🔁 Retry Logic
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))

# 🤖 Optional AI Integration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ✅ Validation
REQUIRED_VARS = {
    "EMAIL_ACCOUNT": EMAIL_ACCOUNT,
    "EMAIL_PASSWORD": EMAIL_PASSWORD,
    "IMAP_SERVER": IMAP_SERVER,
    "SMTP_SERVER": SMTP_SERVER,
    "DB_NAME": DB_NAME,
    "SECRET_KEY": SECRET_KEY
}



missing = [key for key, value in REQUIRED_VARS.items() if not value]
if missing:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
