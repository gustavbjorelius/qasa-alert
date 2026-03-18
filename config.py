# config.py
#
# PURPOSE: One place to load all settings. Evet other file imports from here.
# WHY NOT just use os.getenv() everywhere? Because if you want to rename a variable,
# you'd have to find every file that uses it. Here you change it once. 
#
# HOW IT WORKS: python-dotenv reads your .env fild and loads eaxh line
# as an env var. os.getenv() then reads those variables. 
# Without load_dotenv(), .env would just be a text file Python ignores. 
# 
# WHERE THIS PATTERN COMES FROM: Standard practice in any Python project 
# that needs secrets (passwords, API keys). 

import os 
from dotenv import load_dotenv # pip install python-dotenv

load_dotenv() # reads .env file in current directory, populates os.environ

def _require(key):
    # Helper: crach immediately at startup if a required variable is missing. 
    # WHY: Better to crash with a clear message now than get a confusing error 
    # later when the missing value is actually used. 
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required env var: {key}")
    return value 

# How often to poll. Default 15 minutes if not set in .env 
POLL_INTERVAL_MUNUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))

# Confirmed endpoint from DevTools -> Network -> Headers -> Request URL
# Hard-coded as default so you don't need it in .env
QASA_API_URL     = os.getenv("QASA_API_URL", "https://api.qasa.se/graphql")

# Emaili credentials. _require() crashes if these are missing - good.
SMTP_HOST        = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT        = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER        = _require("SMTP_USER")
SMTP_PASS        = _require("SMTP_PASS")
SMTP_EMAIL       = _require("ALERT_EMAIL")

# Max cost filter. The API already filters this server-side,
# but we re-check locally in filters.py as a safety net.
FILTER_MAX_COUNT = 8900 

