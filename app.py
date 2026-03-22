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
from alerts import save_alert
from dashboard import render_dashboard


#New Change -> import get_asha_by_village
from database import get_asha_by_village
from database import get_asha_by_phone

from tracker import get_progress_update, is_tracker_request
from database import (
    init_db, get_patient, save_patient, get_all_patients,
    save_symptom_log, get_all_asha_alerts, get_alert_count_db,
    save_asha_alert_db
)


def detect_language(text):
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
    return "English"


app = Flask(__name__)

# Initialize database on startup
init_db()


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender       = request.values.get("From", "")
    response     = MessagingResponse()
    msg          = response.message()

    # ── Handle voice notes ────────────────────────────────────────
    try:
        num_media  = int(request.values.get("NumMedia", 0))
        media_url  = request.values.get("MediaUrl0", "")
        media_type = request.values.get("MediaContentType0", "")

        if num_media > 0 and media_url and media_type and "audio" in media_type:
            transcribed = transcribe_voice_note(
                media_url, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
            )
            if transcribed:
                incoming_msg = transcribed
            else:
                msg.body(
                    "Maafi chahti hoon — main aapka voice note samajh "
                    "nahi payi. 🙏\nPlease type your symptom in text."
                )
                return str(response)
    except Exception as e:
        print(f"Voice handling error: {e}")

    # ── Load patient from database ────────────────────────────────
    user = get_patient(sender)

    if not user:
        user = {
            "phone":    sender,
            "name":     "",
            "week":     0,
            "step":     "welcome",
            "language": "Hindi"
        }
        save_patient(sender, "", 0, "welcome")

    # ── Registration Flow ─────────────────────────────────────────
    if incoming_msg.lower() in ["register", "register pregnancy",
                                 "hello", "hi", "start", "namaste"]:

        # Already registered — welcome back!
        if user["step"] == "registered":
            msg.body(
                f"🌸 Welcome back {user['name']}!\n\n"
                f"Aap week {user['week']} mein hain. "
                f"Main hamesha yahan hoon aapke liye. 💚\n\n"
                f"Koi symptom feel ho toh batao, "
                f"ya 'progress' type karo apna update dekhne ke liye! 🌸"
            )
            return str(response)

        # New registration
        user["step"] = "get_name"
        save_patient(sender, "", 0, "get_name")
        msg.body(
            "🌸 Namaste! Welcome to MaaSakhi — "
            "aapki maternal health companion!\n\n"
            "Main aapki pregnancy mein har kadam pe "
            "saath rahungi. 💚\n\n"
            "Pehle mujhe apna naam batao:\n"
            "Please tell me your name:"
        )

    elif user["step"] == "get_name":
        user["name"] = incoming_msg
        user["step"] = "get_week"
        save_patient(sender, incoming_msg, 0, "get_week")
        msg.body(
            f"Namaste {user['name']}! 🙏\n\n"
            f"Aap kitne hafte ki pregnant hain?\n"
            f"How many weeks pregnant are you?\n\n"
            f"Sirf number bhejiye — just type the number\n"
            f"Example: 26"
        )

    elif user["step"] == "get_week":
        try:
            week = int(incoming_msg)
            user["week"] = week
            user["step"] = "get_village"   # NEW STEP
            save_patient(sender, user["name"], week, "get_village")
            msg.body("Aap kis gaon (village) se hain?")
        
        except ValueError:
            msg.body(
                "Sirf number bhejiye please.\n"
                "Just type the number. Example: 26"
            )
    elif user["step"] == "get_village":
        village = incoming_msg.strip()
        asha = get_asha_by_village(village)
        if asha:
            asha_id = asha["asha_id"]
        else:
            asha_id = "default_asha"
        user["step"] = "registered"
        save_patient(
            sender,
            user["name"],
            user["week"],
            "registered",
            user["language"],
            asha_id
        )
        _, tip_msg, _ = analyze("tip", user["week"])
        msg.body(
            f"✅ Aap registered hain, {user['name']}!\n\n"
            f"Village: {village}\n"
            f"Aap week {user['week']} mein hain. "
            f"Main aapke saath hoon 24/7. 💚\n\n"
            f"{tip_msg}\n\n"
            f"Koi bhi symptom feel ho — bas mujhe message karo. "
            f"Main hamesha yahan hoon! 🌸"
        )

    # ── Symptom Analysis ──────────────────────────────────────────
    elif user["step"] == "registered":

        # Update language
        user["language"] = detect_language(incoming_msg)
        save_patient(
            sender, user["name"],
            user["week"], "registered",
            user["language"],
            user.get("asha_id", "default_asha")
        )

        # Check for progress update
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
        level, reply, alert_needed = analyze(
            incoming_msg, user["week"]
        )

        # Save to database
        save_symptom_log(sender, user["week"], incoming_msg, level)

        if level == "RED":
            full_reply = (
                f"{reply}\n\n"
                f"Aapki ASHA worker ko alert kar diya gaya hai.\n"
                f"Please go to your nearest health centre "
                f"immediately. 🏥"
            )
            save_asha_alert_db(
                sender, user["name"],
                user["week"],
                incoming_msg,
                user.get("asha_id", "asha_1")
            )
            save_alert(
                user["name"], user["week"],
                incoming_msg, sender
            )

        elif level == "AMBER":
            full_reply = (
                f"{reply}\n\n"
                f"Agar 24 ghante mein better na ho — "
                f"mujhe zaroor batana. 💛"
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
                f"Paani piyen, rest karein, aur iron ki "
                f"goli lena mat bhoolein! 💚"
            )

        msg.body(full_reply)

    else:
        msg.body(
            "Namaste! 'Register' ya 'Hello' type karke "
            "shuru karein.\n"
            "Type 'Register' to get started with MaaSakhi 🌸"
        )

    return str(response)


# ── ASHA Dashboard ────────────────────────────────────────────────
@app.route("/dashboard/<asha_id>")
def dashboard(asha_id):
    patients  = get_all_patients(asha_id)
    total     = len(patients)
    high_risk = get_alert_count_db()
    safe      = max(total - high_risk, 0)
    return render_dashboard(patients, high_risk, total, safe,asha_id)

#NeW

# ── ASHA Login ────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    from flask import request, redirect

    if request.method == "POST":
        phone = request.form.get("phone")

        asha = get_asha_by_phone(phone)

        if asha:
            return redirect(f"/dashboard/{asha['asha_id']}")
        else:
            return """
            <h3 style='color:red'>❌ Invalid phone number</h3>
            <a href="/login">Try again</a>
            """

    return """
    <html>
    <head>
        <title>ASHA Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial;
                background: #f0faf5;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
            }
            .box {
                background:white;
                padding:30px;
                border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);
                width:90%;
                max-width:350px;
                text-align:center;
            }
            input {
                width:100%;
                padding:12px;
                margin-top:15px;
                border-radius:8px;
                border:1px solid #ccc;
            }
            button {
                margin-top:15px;
                width:100%;
                padding:12px;
                background:#085041;
                color:white;
                border:none;
                border-radius:8px;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🌸 MaaSakhi</h2>
            <p>ASHA Worker Login</p>
            <form method="POST">
                <input name="phone" placeholder="Enter phone (with whatsapp:+91...)" required />
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """
# ── Health Check ──────────────────────────────────────────────────
@app.route("/")
def home():
    return (
        "🌸 MaaSakhi is running!\n "
        "Visit /login for the ASHA worker login\n"
        "Visit /dashboard for the ASHA worker dashboard."
    )


# ── Run ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)



