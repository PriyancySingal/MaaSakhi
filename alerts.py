# ─────────────────────────────────────────────────────────────────
# MaaSakhi ASHA Alert System
# Sends real WhatsApp alert to the CORRECT ASHA worker
# ─────────────────────────────────────────────────────────────────

import os
from datetime import datetime
from twilio.rest import Client

TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"


def send_whatsapp_alert(name, week, symptom, phone, asha_number):
    """Send real WhatsApp message to the correct ASHA worker."""
    if not asha_number:
        print("No ASHA number provided — skipping WhatsApp alert")
        return False

    # Make sure number has whatsapp: prefix
    if not asha_number.startswith("whatsapp:"):
        asha_number = "whatsapp:" + asha_number

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
            to=asha_number,
            body=alert_message
        )

        print(f"WhatsApp alert sent to {asha_number}! SID: {message.sid}")
        return True

    except Exception as e:
        print(f"Failed to send WhatsApp alert: {e}")
        return False


def save_alert(name, week, symptom, phone, asha_id=None):
    """
    Sends real WhatsApp alert to the correct ASHA worker.
    Looks up ASHA worker phone from database using asha_id.
    """
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

    # Get ASHA worker phone from database
    asha_number = None

    if asha_id and asha_id != "default_asha":
        try:
            from database import get_asha_by_phone, engine
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT phone FROM asha_workers WHERE asha_id = :id"),
                    {"id": asha_id}
                ).fetchone()
                if result:
                    asha_number = result.phone
                    print(f"Found ASHA worker phone: {asha_number}")
        except Exception as e:
            print(f"Error getting ASHA phone: {e}")

    # Fallback to environment variable
    if not asha_number:
        asha_number = os.environ.get("ASHA_NUMBER", "")
        print(f"Using fallback ASHA_NUMBER: {asha_number}")

    # Send WhatsApp
    if asha_number:
        send_whatsapp_alert(name, week, symptom, phone, asha_number)
    else:
        print("No ASHA number found — skipping WhatsApp alert")