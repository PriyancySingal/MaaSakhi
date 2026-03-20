import os

# Twilio credentials — set these in Railway environment variables
TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# App settings
DEBUG = os.environ.get("DEBUG", "True") == "True"
PORT  = int(os.environ.get("PORT", 5000))

# ASHA worker number
ASHA_WORKER_NUMBER = os.environ.get("ASHA_NUMBER", "")