import os 
from dotenv import load_dotenv

load_dotenv()

def _require(key):
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required env var: {key}")
    return value 

QASA_API_URL     = os.getenv("QASA_API_URL", "https://api.qasa.se/graphql")
SMTP_HOST        = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT        = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER        = _require("SMTP_USER")
SMTP_PASS        = _require("SMTP_PASS")
SMTP_EMAIL       = _require("ALERT_EMAIL")
FILTER_MAX_COUNT = 8900 

