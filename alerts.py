import os
import urllib.parse
from datetime import datetime
from twilio.rest import Client

TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"


def _send(to, body):
    try:
        Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).messages.create(
            from_=TWILIO_WHATSAPP_NUMBER, to=to, body=body
        )
        return True
    except Exception as e:
        print("[alerts] WhatsApp send failed to " + str(to) + ": " + str(e))
        return False


def _wa(phone):
    if phone.startswith("whatsapp:"):
        return phone
    clean = phone.replace(" ", "").replace("-", "")
    if not clean.startswith("+"):
        clean = "+91" + clean.lstrip("0")
    return "whatsapp:" + clean


def _maps_link(address, village):
    location = (address or village or "").strip()
    if not location:
        return ""
    encoded = urllib.parse.quote(location + ", India")
    return "https://www.google.com/maps/dir/?api=1&destination=" + encoded


def send_whatsapp_alert(name, week, symptom, phone, asha_number, address="", village=""):
    maps_url  = _maps_link(address, village)
    maps_line = "📌 Navigate to patient: " + maps_url if maps_url else ""
    addr_line = address if address else "Not provided"
    time_str  = datetime.now().strftime("%d %b %Y, %I:%M %p")

    body = (
        "🚨 HIGH RISK ALERT — MaaSakhi\n\n"
        + "👩 Patient: " + name + "\n"
        + "🤰 Pregnancy Week: " + str(week) + "\n"
        + "⚠️ Symptom: " + symptom + "\n"
        + "📞 Phone: " + phone + "\n"
        + "📍 Village: " + village + "\n"
        + "🏠 Address: " + addr_line + "\n"
        + "🕐 Time: " + time_str + "\n\n"
        + maps_line + "\n\n"
        + "Please contact her immediately!"
    )
    result = _send(_wa(asha_number), body)
    if result:
        print("[alerts] RED alert sent to " + asha_number)
    return result


def save_alert(name, week, symptom, phone, asha_id=None, address="", village=""):
    time_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    print("HIGH RISK ALERT — MaaSakhi")
    print("Patient : " + str(name))
    print("Week    : " + str(week))
    print("Symptom : " + str(symptom))
    print("Phone   : " + str(phone))
    print("Time    : " + time_str)
    print("Action  : Contact immediately!")

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
                    print("[alerts] Found ASHA phone: " + asha_number)
        except Exception as e:
            print("[alerts] DB lookup error: " + str(e))

    if not asha_number:
        asha_number = os.environ.get("ASHA_NUMBER", "")
        print("[alerts] Using fallback ASHA_NUMBER: " + asha_number)

    if asha_number:
        send_whatsapp_alert(name, week, symptom, phone, asha_number, address, village)
    else:
        print("[alerts] No ASHA number found — skipping WhatsApp alert")


def send_attend_confirmation(patient_phone, patient_name, asha_name):
    body = (
        "🌸 Namaste " + patient_name + "!\n\n"
        + asha_name + " ne aapka case attend kar liya hai. 💚\n\n"
        + "Kya aap ab theek feel kar rahi hain?\n\n"
        + "✅ 'I am better' — agar theek hain\n"
        + "⚠️ 'Still not feeling well' — agar takleef abhi bhi hai"
    )
    return _send(_wa(patient_phone), body)


def send_referral_notification(patient_phone, patient_name, referred_to):
    body = (
        "🌸 " + patient_name + ", aapki ASHA worker ne aapko "
        + referred_to + " ke liye refer kar diya hai.\n\n"
        + "Please jald se jald wahan jaayein. 🏥"
    )
    return _send(_wa(patient_phone), body)


def send_delivery_notification(asha_phone, patient_name, patient_phone, delivery_date):
    body = (
        "👶 Delivery Registered — MaaSakhi\n\n"
        + "Patient : " + patient_name + "\n"
        + "Phone   : " + patient_phone + "\n"
        + "Date    : " + delivery_date + "\n\n"
        + "Please schedule the Day 1 PNC visit. 🌸"
    )
    return _send(_wa(asha_phone), body)


def send_pnc_confirmation(patient_phone, patient_name):
    body = (
        "✅ " + patient_name + ", aapki aaj ki PNC visit record ho gayi. 🌸\n"
        + "Koi bhi problem ho toh mujhe batao. 💚"
    )
    return _send(_wa(patient_phone), body)


def send_vaccine_confirmation(patient_phone, patient_name, vaccine_name):
    body = (
        "💉 " + patient_name + ", aapke bacche ko aaj "
        + vaccine_name + " vaccine lagi. ✅\n\n"
        + "Agle teeke ke liye ASHA worker aapko batayegi. 🌸"
    )
    return _send(_wa(patient_phone), body)


def send_growth_alert(asha_phone, child_id, mother_phone, weight_kg, age_months, z_score, status):
    body = (
        "⚠️ Growth Alert — MaaSakhi\n\n"
        + "Child ID : " + str(child_id) + "\n"
        + "Mother   : " + mother_phone + "\n"
        + "Weight   : " + str(weight_kg) + " kg at " + str(age_months) + " months\n"
        + "Z-score  : " + str(z_score) + " — " + status + "\n\n"
        + "Please refer to NRC if needed. 🏥"
    )
    return _send(_wa(asha_phone), body)


def send_bmo_resolved(patient_phone, patient_name):
    body = (
        "✅ " + patient_name + ", aapka case Block Medical Officer ne "
        + "resolve kar diya hai. 💚\nApna khayal rakhein! 🌸"
    )
    return _send(_wa(patient_phone), body)