# ─────────────────────────────────────────────────────────────────
# MaaSakhi — Main Application
# WhatsApp Maternal Health Bot for Rural India
# Built for WitchHunt Hackathon 2026
# ─────────────────────────────────────────────────────────────────
import os
from flask import Flask, request, render_template_string, session, redirect
from twilio.twiml.messaging_response import MessagingResponse
from config import PORT, DEBUG, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from voice import transcribe_voice_note
from analyzer import analyze
from alerts import save_alert
from dashboard import render_dashboard
from database import update_alert_status, get_alert_by_patient_phone
from database import get_asha_by_village, get_asha_by_phone
from tracker import get_progress_update, is_tracker_request
from database import (
    init_db, get_patient, save_patient, get_all_patients,
    save_symptom_log, get_all_asha_alerts, get_alert_count_db,
    save_asha_alert_db
)
from admin import render_admin_login, render_admin_panel
from database import (
    verify_admin, add_asha_worker,
    toggle_asha_status, delete_asha_worker,
    get_all_alerts_admin
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
app.secret_key = os.environ.get("SECRET_KEY", "maasakhi2026secret")


HOMEPAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MaaSakhi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin:0; background:#f0faf5; color:#2c2c2a; }
        .hero { background:#085041; color:white; padding:40px 20px; }
        .hero-content {
            display:flex; justify-content:space-between; align-items:center;
            max-width:1000px; margin:auto; gap:20px;
        }
        .hero-text h1 { font-size:32px; }
        .hero-text h2 { font-size:18px; font-weight:400; margin-top:8px; }
        .hero-text p  { margin-top:10px; font-size:14px; opacity:0.9; }
        .hero-logo img {
            width:140px;
            filter: drop-shadow(0px 4px 8px rgba(0,0,0,0.3));
        }
        .section { padding:30px 20px; text-align:center; }
        .features {
            display:grid; grid-template-columns:repeat(2,1fr);
            gap:12px; margin-top:20px;
        }
        .card { background:white; padding:15px; border-radius:10px; border:1px solid #e1f5ee; }
        .btn {
            display:inline-block; margin-top:20px; padding:14px 24px;
            background:#085041; color:white; text-decoration:none;
            border-radius:8px; font-weight:bold;
        }
        .btn-admin { background:#2D1267; border:1px solid #5B2FBF; margin-top:20px; }
        .btn-admin:hover { background:#3D1A8C; }
        .footer { text-align:center; font-size:12px; color:#777; padding:20px; }
        @media (max-width: 768px) {
            .hero-content { flex-direction:column; text-align:center; }
            .hero-logo img { width:100px; margin-top:15px; }
        }
    </style>
</head>
<body>

<div class="hero">
    <div class="hero-content">
        <div class="hero-text">
            <h1>🌿 MaaSakhi</h1>
            <h2>Maternal Health Support System for Rural India</h2>
            <p>In collaboration with Department of Women & Child Development</p>
        </div>
        <div class="hero-logo">
            <img src="/static/logo.png" alt="MaaSakhi Logo">
        </div>
    </div>
</div>

<div class="section">
    <p>
        MaaSakhi is an AI-powered WhatsApp assistant that helps pregnant women
        and supports ASHA workers with real-time health monitoring and risk detection.
    </p>
    <div class="features">
        <div class="card">📱 WhatsApp Monitoring</div>
        <div class="card">🚨 Risk Alerts</div>
        <div class="card">👩‍⚕️ ASHA Dashboard</div>
        <div class="card">🌍 Multi-language Support</div>
    </div>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:20px">
        <a href="/login" class="btn">👩 Login as ASHA Worker</a>
        <a href="/admin/login" class="btn btn-admin">🔐 Admin Login</a>
    </div>
</div>

<div class="footer">
    Built for WitchHunt 2026 • Powered by WHO + NHM + FOGSI Guidelines
</div>

</body>
</html>
"""


# Initialize database on startup
init_db()


# ── Patient confirms recovery check ──────────────────────────────
def handle_recovery_confirmation(sender, user, msg):
    """Check if patient is confirming recovery."""
    recovery_keywords = [
        "i am better", "i am fine", "theek hoon", "theek hu",
        "better now", "feeling better", "mujhe theek", "ab theek",
        "recovered", "all good", "sahi hoon", "achha feel"
    ]
    msg_lower = msg.lower()
    return any(keyword in msg_lower for keyword in recovery_keywords)


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
            user["step"] = "get_village"
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
            sender, user["name"], user["week"],
            "registered", user["language"], asha_id, village
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

        # ── Check if patient is confirming recovery ───────────────
        if handle_recovery_confirmation(sender, user, incoming_msg):
            alert = get_alert_by_patient_phone(sender)
            if alert and alert["status"] == "Attended":
                update_alert_status(alert["id"], "Resolved")
                msg.body(
                    f"🌸 Bahut khushi hui yeh sunke, {user['name']}!\n\n"
                    f"Aapki recovery confirm ho gayi. ✅\n"
                    f"Aapki ASHA worker ko bhi inform kar diya gaya hai.\n\n"
                    f"Apna khayal rakhein aur iron ki goli lena mat bhoolein! 💚"
                )
                return str(response)
            elif alert and alert["status"] == "Pending":
                msg.body(
                    f"Khushi hui sunke {user['name']}! 🌸\n\n"
                    f"Aapki ASHA worker abhi aapke case ko review kar rahi hain.\n"
                    f"Agar koi aur symptom ho toh zaroor batana. 💚"
                )
                return str(response)

        # Update language
        user["language"] = detect_language(incoming_msg)
        save_patient(
            sender, user["name"],
            user["week"], "registered",
            user["language"],
            user.get("asha_id", "default_asha"),
            user.get("village", "")
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
                user["week"], incoming_msg,
                user.get("asha_id", "default_asha")
            )
            save_alert(
                user["name"], user["week"],
                incoming_msg, sender,
                user.get("asha_id", "default_asha")
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
    alerts    = get_all_asha_alerts(asha_id)
    high_risk = len(alerts)
    safe      = max(total - high_risk, 0)
    return render_dashboard(patients, high_risk, total, safe, asha_id)


# ── ASHA marks alert as Attended ─────────────────────────────────
@app.route("/dashboard/<asha_id>/attend/<alert_id>", methods=["POST"])
def mark_attended(asha_id, alert_id):
    update_alert_status(int(alert_id), "Attended")
    return redirect(f"/dashboard/{asha_id}")


# ── ASHA Login ────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        # Auto add whatsapp: prefix if missing
        if not phone.startswith("whatsapp:"):
            phone = "whatsapp:+91" + phone.replace("+91", "").replace(" ", "")
        asha = get_asha_by_phone(phone)
        if asha:
            return redirect(f"/dashboard/{asha['asha_id']}")
        else:
            return """
            <h3 style='color:red;font-family:Arial;padding:20px'>
                ❌ Invalid phone number. Try again.
            </h3>
            <a href="/login" style='font-family:Arial;padding:20px'>← Back</a>
            """

    return """
    <html>
    <head>
        <title>ASHA Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial; background:#f0faf5;
                display:flex; justify-content:center;
                align-items:center; height:100vh;
            }
            .box {
                background:white; padding:30px; border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);
                width:90%; max-width:350px; text-align:center;
            }
            input {
                width:100%; padding:12px; margin-top:15px;
                border-radius:8px; border:1px solid #ccc;
                box-sizing:border-box;
            }
            button {
                margin-top:15px; width:100%; padding:12px;
                background:#085041; color:white;
                border:none; border-radius:8px;
                font-size:14px; font-weight:bold; cursor:pointer;
            }
            .hint { font-size:11px; color:#888; margin-top:8px; }
            .back { display:block; margin-top:16px; font-size:12px; color:#555; text-decoration:none; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🌿 MaaSakhi</h2>
            <p>ASHA Worker Login</p>
            <form method="POST">
                <input name="phone" placeholder="Enter your 10-digit mobile number" required />
                <p class="hint">Example: 9315168344</p>
                <button type="submit">Login</button>
            </form>
            <a href="/" class="back">← Back to Home</a>
        </div>
    </body>
    </html>
    """


# ── Homepage ──────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template_string(HOMEPAGE_HTML)


# ── Admin Login ───────────────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = verify_admin(username, password)
        if admin:
            session["admin"] = admin
            return redirect("/admin")
        return render_admin_login(error="Invalid username or password")
    return render_admin_login()


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")


# ── Admin Dashboard ───────────────────────────────────────────────
@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin/login")
    tab = request.args.get("tab", "asha")
    return render_admin_panel(
        admin_name=session["admin"]["name"],
        tab=tab
    )


# ── Add ASHA Worker ───────────────────────────────────────────────
@app.route("/admin/add-asha", methods=["POST"])
def admin_add_asha():
    if "admin" not in session:
        return redirect("/admin/login")
    asha_id  = request.form.get("asha_id", "").strip()
    name     = request.form.get("name", "").strip()
    phone    = request.form.get("phone", "").strip()
    village  = request.form.get("village", "").strip()
    district = request.form.get("district", "").strip()
    success  = add_asha_worker(asha_id, name, phone, village, district)
    return render_admin_panel(
        admin_name=session["admin"]["name"],
        tab="asha",
        message="ASHA worker added successfully!" if success else "Failed to add ASHA worker.",
        success=success
    )


# ── Toggle ASHA Status ────────────────────────────────────────────
@app.route("/admin/toggle-asha", methods=["POST"])
def admin_toggle_asha():
    if "admin" not in session:
        return redirect("/admin/login")
    asha_id = request.form.get("asha_id")
    toggle_asha_status(asha_id)
    return redirect("/admin?tab=asha")


# ── Delete ASHA Worker ────────────────────────────────────────────
@app.route("/admin/delete-asha", methods=["POST"])
def admin_delete_asha():
    if "admin" not in session:
        return redirect("/admin/login")
    asha_id = request.form.get("asha_id")
    delete_asha_worker(asha_id)
    return redirect("/admin?tab=asha")


# ── Run ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
