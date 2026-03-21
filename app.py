# ─────────────────────────────────────────────────────────────────
# MaaSakhi — Main Application
# WhatsApp Maternal Health Bot for Rural India
# Built for WitchHunt Hackathon 2026
# ─────────────────────────────────────────────────────────────────

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from config import PORT, DEBUG, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from voice import transcribe_voice_note
from analyzer import analyze
from alerts import save_alert, get_alert_count
from dashboard import render_dashboard
from tracker import get_progress_update, is_tracker_request
from health_log import log_symptom


def detect_language(text):
    """Simple language detection based on script."""
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return "Hindi"
        elif '\u0B80' <= char <= '\u0BFF':
            return "Tamil"
        elif '\u0C00' <= char <= '\u0C7F':
            return "Telugu"
        elif '\u0980' <= char <= '\u09FF':
            return "Bengali"
        elif '\u0A80' <= char <= '\u0AFF':
            return "Gujarati"
        elif '\u0C80' <= char <= '\u0CFF':
            return "Kannada"
        elif '\u0900' <= char <= '\u097F':
            return "Marathi"
    return "English"



app = Flask(__name__)

user_profiles = {}


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender       = request.values.get("From", "")
    response     = MessagingResponse()
    msg          = response.message()

    # ── Handle voice notes safely ─────────────────────────────────
    try:
        num_media  = int(request.values.get("NumMedia", 0))
        media_url  = request.values.get("MediaUrl0", "")
        media_type = request.values.get("MediaContentType0", "")

        if num_media > 0 and media_url and media_type and "audio" in media_type:
            transcribed = transcribe_voice_note(
                media_url,
                TWILIO_ACCOUNT_SID,
                TWILIO_AUTH_TOKEN
            )
            if transcribed:
                incoming_msg = transcribed
            else:
                msg.body(
                    "Maafi chahti hoon — main aapka voice note samajh nahi payi. 🙏\n"
                    "Please type your symptom in text."
                )
                return str(response)
    except Exception as e:
        print(f"Voice handling error: {e}")

    # ── Register new user ─────────────────────────────────────────
    if sender not in user_profiles:
        user_profiles[sender] = {
            "step": "welcome",
            "name": "",
            "week": 0,
            "language": "Hindi"
        }

    user = user_profiles[sender]

    # ── Registration Flow ─────────────────────────────────────────
    if incoming_msg.lower() in ["register", "register pregnancy",
                                 "hello", "hi", "start", "namaste"]:
        user["step"] = "get_name"
        msg.body(
            "🌸 Namaste! Welcome to MaaSakhi — aapki maternal health companion!\n\n"
            "Main aapki pregnancy mein har kadam pe saath rahungi. 💚\n\n"
            "Pehle mujhe apna naam batao:\n"
            "Please tell me your name:"
        )

    elif user["step"] == "get_name":
        user["name"] = incoming_msg
        user["step"] = "get_week"
        msg.body(
            f"Namaste {user['name']}! 🙏\n\n"
            f"Aap kitne hafte ki pregnant hain?\n"
            f"How many weeks pregnant are you?\n\n"
            f"Sirf number bhejiye — just type the number\n"
            f"Example: 26"
        )

    elif user["step"] == "get_week":
        try:
            user["week"] = int(incoming_msg)
            user["step"] = "registered"
            _, tip_msg, _ = analyze("tip", user["week"])
            msg.body(
                f"✅ Aap registered hain, {user['name']}!\n\n"
                f"Aap week {user['week']} mein hain. "
                f"Main aapke saath hoon 24/7. 💚\n\n"
                f"{tip_msg}\n\n"
                f"Koi bhi symptom feel ho — bas mujhe message karo. "
                f"Main hamesha yahan hoon! 🌸"
            )
        except ValueError:
            msg.body(
                "Sirf number bhejiye please.\n"
                "Just type the number. Example: 26"
            )

    # ── Symptom Analysis ──────────────────────────────────────────
    elif user["step"] == "registered":
        # Update language based on what woman is using
        user["language"] = detect_language(incoming_msg)

        # Check if asking for progress update first
        if is_tracker_request(incoming_msg):
            reply = get_progress_update(
                user["week"],
                user["name"],
                sender,
                user["language"]
            )
            msg.body(reply)
            return str(response)

        # Analyze symptom
        level, reply, alert_needed = analyze(incoming_msg, user["week"])

        # Log every report to her personal health record
        log_symptom(sender, user["week"], incoming_msg, level)

        if level == "RED":
            full_reply = (
                f"{reply}\n\n"
                f"Aapki ASHA worker ko alert kar diya gaya hai.\n"
                f"Please go to your nearest health centre immediately. 🏥"
            )
            save_alert(user["name"], user["week"], incoming_msg, sender)

        elif level == "AMBER":
            full_reply = (
                f"{reply}\n\n"
                f"Agar 24 ghante mein better na ho — mujhe zaroor batana. 💛"
            )

        elif level == "MYTH":
            full_reply = reply

        elif level == "TIP":
            full_reply = (
                f"{reply}\n\n"
                f"Koi symptom feel ho toh mujhe batao! 🌸"
            )

        else:
            full_reply = (
                f"{reply}\n\n"
                f"Paani piyen, rest karein, aur iron ki goli lena mat bhoolein! 💚"
            )

        msg.body(full_reply)

    else:
        msg.body(
            "Namaste! 'Register' ya 'Hello' type karke shuru karein.\n"
            "Type 'Register' to get started with MaaSakhi 🌸"
        )

    return str(response)


# ── ASHA Dashboard ────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    total     = sum(1 for p in user_profiles.values() if p.get("step") == "registered")
    high_risk = get_alert_count()
    safe      = max(total - high_risk, 0)
    return render_dashboard(user_profiles, high_risk, total, safe)


# ── Health Check ──────────────────────────────────────────────────
@app.route("/")
def home():
    return "🌸 MaaSakhi is running! Visit /dashboard for the ASHA worker dashboard."


# ── Run ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

