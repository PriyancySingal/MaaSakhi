# ─────────────────────────────────────────────────────────────────
# MaaSakhi ASHA Alert System
# Now uses PostgreSQL database for permanent storage
# + Sends real WhatsApp alerts to ASHA worker
# ─────────────────────────────────────────────────────────────────

import os
from datetime import datetime
from twilio.rest import Client

TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
ASHA_WORKER_NUMBER     = os.environ.get("ASHA_NUMBER", "")


def send_whatsapp_alert(name, week, symptom, phone):
    """Send real WhatsApp message to ASHA worker."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        alert_message = (
            f"🚨 HIGH RISK ALERT — MaaSakhi\n\n"
            f"Patient: {name}\n"
            f"Pregnancy Week: {week}\n"
            f"Reported: {symptom}\n"
            f"Phone: {phone}\n"
            f"Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"⚠️ Please contact her immediately!\n"
            f"Based on WHO ANC 2016 danger signs."
        )

        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=ASHA_WORKER_NUMBER,
            body=alert_message
        )

        print(f"ASHA WhatsApp alert sent! SID: {message.sid}")
        return True

    except Exception as e:
        print(f"Failed to send WhatsApp alert: {e}")
        return False


def save_alert(name, week, symptom, phone):
    """
    Sends real WhatsApp alert to ASHA worker.
    Database saving is handled by save_asha_alert_db in app.py.
    """
    # Print to terminal
    print(f"""
╔══════════════════════════════════════╗
  ⚠️  HIGH RISK ALERT — MaaSakhi
╠══════════════════════════════════════╣
  Patient : {name}
  Week    : {week}
  Symptom : {symptom}
  Phone   : {phone}
  Time    : {datetime.now().strftime("%d %b %Y, %I:%M %p")}
  Action  : Contact immediately!
╚══════════════════════════════════════╝
""")

    # Send real WhatsApp to ASHA worker
    if ASHA_WORKER_NUMBER:
        send_whatsapp_alert(name, week, symptom, phone)
    else:
        print("ASHA_NUMBER not set — skipping WhatsApp alert")
