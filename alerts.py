# ─────────────────────────────────────────────────────────────────
# alerts.py — MaaSakhi
# All outbound WhatsApp notifications:
#   - RED alert to ASHA worker (with Maps link + DB lookup)
#   - Attend confirmation to patient
#   - Referral notification to patient
#   - Delivery registered → ASHA
#   - PNC visit confirmed → patient
#   - Vaccine given → patient
#   - Growth alert → ASHA
#   - BMO resolved → patient
# ─────────────────────────────────────────────────────────────────

import os
import urllib.parse
from datetime import datetime
from twilio.rest import Client

TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _send(to: str, body: str) -> bool:
    """Fire-and-forget WhatsApp sender. Never raises."""
    try:
        Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).messages.create(
            from_=TWILIO_WHATSAPP_NUMBER, to=to, body=body
        )
        return True
    except Exception as e:
        print(f"[alerts] WhatsApp send failed → {to}: {e}")
        return False


def _wa(phone: str) -> str:
    """Normalise any phone format to whatsapp:+91XXXXXXXXXX."""
    if phone.startswith("whatsapp:"):
        return phone
    clean = phone.replace(" ", "").replace("-", "")
    if not clean.startswith("+"):
        clean = "+91" + clean.lstrip("0")
    return "whatsapp:" + clean


def _maps_link(address: str, village: str) -> str:
    location = (address or village or "").strip()
    if not location:
        return ""
    encoded = urllib.parse.quote(location + ", India")
    return f"https://www.google.com/maps/dir/?api=1&destination={encoded}"


# ─────────────────────────────────────────────────────────────────
# RED ALERT — send WhatsApp to ASHA worker directly
# ─────────────────────────────────────────────────────────────────

def send_whatsapp_alert(name, week, symptom, phone, asha_number,
                        address="", village=""):
    """Send a HIGH RISK alert to a known ASHA WhatsApp number."""
    maps_url  = _maps_link(address, village)
    maps_line = f"📌 Navigate to patient: {maps_url}" if maps_url else ""

    body = (
        f"🚨 HIGH RISK ALERT — MaaSakhi\n\n"
        f"👩 Patient: {name}\n"
        f"🤰 Pregnancy Week: {week}\n"
        f"⚠️ Symptom: {symptom}\n"
        f"📞 Phone: {phone}\n"
        f"📍 Village: {village}\n"
        f"🏠 Address: {address if address else 'Not provided'}\n"
        f"🕐 Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
        f"{maps_line}\n\n"
        f"Please contact her immediately!"
    )
    result = _send(_wa(asha_number), body)
    if result:
        print(f"[alerts] RED alert sent to {asha_number}")
    return result


def save_alert(name, week, symptom, phone, asha_id=None,
               address="", village=""):
    """
    Looks up the ASHA worker phone from DB using asha_id,
    then fires send_whatsapp_alert(). Falls back to ASHA_NUMBER env var.
    Called from main.py when level == 'RED'.
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

    asha_number = None

    if asha_id and asha_id != "default_asha":
        try:
            from database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT phone FROM asha_workers WHERE asha_id = :id"),
                    {"id": asha_id}
                ).fetchone()
                if row:
                    asha_number = row.phone
                    print(f"[alerts] Found ASHA phone: {asha_number}")
        except Exception as e:
            print(f"[alerts] DB lookup error: {e}")

    if not asha_number:
        asha_number = os.environ.get("ASHA_NUMBER", "")
        print(f"[alerts] Using fallback ASHA_NUMBER: {asha_number}")

    if asha_number:
        send_whatsapp_alert(name, week, symptom, phone, asha_number,
                            address, village)
    else:
        print("[alerts] No ASHA number found — skipping WhatsApp alert")


# ─────────────────────────────────────────────────────────────────
# ATTEND CONFIRMATION — patient told ASHA is coming
# ─────────────────────────────────────────────────────────────────

def send_attend_confirmation(patient_phone: str, patient_name: str,
                             asha_name: str) -> bool:
    return _send(_wa(patient_phone), (
        f"🌸 Namaste *{patient_name}*!\n\n"
        f"*{asha_name}* ne aapka case attend kar liya hai. 💚\n\n"
        "Kya aap ab theek feel kar rahi hain?\n\n"
        "✅ *'I am better'* — agar theek hain\n"
        "⚠️ *'Still not feeling well'* — agar takleef abhi bhi hai"
    ))


# ─────────────────────────────────────────────────────────────────
# REFERRAL — patient told she has been referred
# ─────────────────────────────────────────────────────────────────

def send_referral_notification(patient_phone: str, patient_name: str,
                               referred_to: str) -> bool:
    return _send(_wa(patient_phone), (
        f"🌸 *{patient_name}*, aapki ASHA worker ne aapko "
        f"*{referred_to}* ke liye refer kar diya hai.\n\n"
        "Please jald se jald wahan jaayein. 🏥"
    ))


# ─────────────────────────────────────────────────────────────────
# DELIVERY REGISTERED — ASHA told to schedule Day 1 PNC
# ─────────────────────────────────────────────────────────────────

def send_delivery_notification(asha_phone: str, patient_name: str,
                               patient_phone: str, delivery_date: str) -> bool:
    return _send(_wa(asha_phone), (
        f"👶 *Delivery Registered — MaaSakhi*\n\n"
        f"Patient : {patient_name}\n"
        f"Phone   : {patient_phone}\n"
        f"Date    : {delivery_date}\n\n"
        "Please schedule the Day 1 PNC visit. 🌸"
    ))


# ─────────────────────────────────────────────────────────────────
# PNC VISIT CONFIRMED — patient notified
# ─────────────────────────────────────────────────────────────────

def send_pnc_confirmation(patient_phone: str, patient_name: str) -> bool:
    return _send(_wa(patient_phone), (
        f"✅ *{patient_name}*, aapki aaj ki PNC visit record ho gayi. 🌸\n"
        "Koi bhi problem ho toh mujhe batao. 💚"
    ))


# ─────────────────────────────────────────────────────────────────
# VACCINE GIVEN — patient notified
# ─────────────────────────────────────────────────────────────────

def send_vaccine_confirmation(patient_phone: str, patient_name: str,
                              vaccine_name: str) -> bool:
    return _send(_wa(patient_phone), (
        f"💉 *{patient_name}*, aapke bacche ko aaj "
        f"*{vaccine_name}* vaccine lagi. ✅\n\n"
        "Agle teeke ke liye ASHA worker aapko batayegi. 🌸"
    ))


# ─────────────────────────────────────────────────────────────────
# GROWTH ALERT — ASHA notified of underweight child
# ─────────────────────────────────────────────────────────────────

def send_growth_alert(asha_phone: str, child_id: int, mother_phone: str,
                      weight_kg: float, age_months: int,
                      z_score: float, status: str) -> bool:
    return _send(_wa(asha_phone), (
        f"⚠️ *Growth Alert — MaaSakhi*\n\n"
        f"Child ID : {child_id}\n"
        f"Mother   : {mother_phone}\n"
        f"Weight   : {weight_kg} kg at {age_months} months\n"
        f"Z-score  : {z_score} — *{status}*\n\n"
        "Please refer to NRC if needed. 🏥"
    ))


# ─────────────────────────────────────────────────────────────────
# BMO RESOLVED — patient notified
# ─────────────────────────────────────────────────────────────────

def send_bmo_resolved(patient_phone: str, patient_name: str) -> bool:
    return _send(_wa(patient_phone), (
        f"✅ *{patient_name}*, aapka case Block Medical Officer ne "
        "resolve kar diya hai. 💚\nApna khayal rakhein! 🌸"
    ))