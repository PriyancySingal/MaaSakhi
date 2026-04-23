# ─────────────────────────────────────────────────────────────────
# MaaSakhi — Main Application
# WhatsApp Maternal Health Bot for Rural India
# Built for WitchHunt Hackathon 2026
# ─────────────────────────────────────────────────────────────────

import os
from flask import Flask, request, render_template_string, session, redirect
from twilio.twiml.messaging_response import MessagingResponse

# ── All imports grouped cleanly ───────────────────────────────────
from config import PORT, DEBUG, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from voice   import transcribe_voice_note
from analyzer import analyze, detect_language_from_text as detect_language
from alerts  import save_alert
from dashboard import render_dashboard
from tracker import get_progress_update, is_tracker_request
from admin   import render_admin_login, render_admin_panel
from escalation import start_escalation_engine

from database import (
    # Core
    init_db,
    # Patient
    get_patient, save_patient,
    get_all_patients, get_all_patients_admin,
    save_symptom_log,
    # ASHA Worker
    get_asha_by_village, get_asha_by_phone,
    get_all_asha_workers,
    add_asha_worker, toggle_asha_status, delete_asha_worker,
    get_asha_stats,
    # Supervisor
    verify_supervisor,
    add_asha_supervisor, get_all_supervisors,
    get_supervisor_stats, get_supervisor_ashas,
    get_supervisor_alerts,
    # BMO
    verify_bmo,
    add_block_officer, get_all_block_officers,
    get_bmo_stats, get_bmo_alerts,
    # Admin / DHO
    verify_admin, get_district_stats,
    get_all_alerts_admin,
    # Alerts
    save_asha_alert_db, get_all_asha_alerts,
    get_alert_count_db, update_alert_status,
    get_alert_by_patient_phone, get_alert_by_id,
    escalate_alert,
    # Visits
    save_asha_visit, get_asha_visits,
    # Unified login
    unified_login,
)

# ─────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "maasakhi2026secret")

# Initialize database AFTER app is created
init_db()

# Start escalation engine in background thread
start_escalation_engine()

# ─────────────────────────────────────────────────────────────────
# HOMEPAGE
# ─────────────────────────────────────────────────────────────────

HOMEPAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MaaSakhi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Poppins',sans-serif; background:#f7faf9; color:#1f2937; }

        .navbar {
            display:flex; justify-content:space-between; align-items:center;
            padding:16px 40px; background:white;
            box-shadow:0 2px 8px rgba(0,0,0,0.05);
        }
        .nav-title { font-weight:600; font-size:20px; color:#085041; }
        .nav-links a {
            margin-left:20px; text-decoration:none;
            color:#444; font-size:14px; font-weight:500;
        }
        .nav-links a:hover { color:#085041; }

        .hero {
            background:linear-gradient(135deg,#085041,#0a6b52);
            color:white; padding:80px 20px;
        }
        .hero-container {
            max-width:1100px; margin:auto;
            display:flex; justify-content:space-between;
            align-items:center; gap:40px; flex-wrap:wrap;
        }
        .hero-text { max-width:500px; }
        .hero-text h1 { font-size:38px; font-weight:600; }
        .hero-text p  { margin-top:12px; font-size:16px; opacity:0.9; }
        .hero-buttons { margin-top:20px; }

        .btn {
            display:inline-block; padding:12px 22px; border-radius:8px;
            text-decoration:none; font-size:14px; font-weight:600;
            margin-right:10px; margin-top:8px;
        }
        .btn-primary   { background:white; color:#085041; }
        .btn-secondary { background:#2D1267; color:white; }
        .btn-warning   { background:#B45309; color:white; }
        .btn-info      { background:#0369A1; color:white; }

        .hero img {
            width:160px;
            filter:drop-shadow(0px 6px 14px rgba(0,0,0,0.3));
        }

        .trust {
            text-align:center; padding:30px 20px;
            font-size:14px; color:#555;
        }
        .trust span { margin:0 10px; }

        .features {
            padding:50px 20px; max-width:1000px;
            margin:auto; text-align:center;
        }
        .features h2 { font-size:24px; color:#085041; }
        .feature-grid {
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
            gap:16px; margin-top:30px;
        }
        .card {
            background:white; padding:18px; border-radius:14px;
            box-shadow:0 6px 18px rgba(0,0,0,0.08); transition:0.2s;
        }
        .card:hover { transform:translateY(-5px); }

        .flow { text-align:center; padding:60px 20px; }
        .flow h2 { font-size:26px; color:#085041; }
        .flow-subtext {
            margin-top:10px; font-size:14px; color:#666;
            max-width:700px; margin-left:auto; margin-right:auto;
        }
        .flow-grid {
            margin-top:40px; display:flex; align-items:center;
            justify-content:center; flex-wrap:wrap; gap:14px;
        }
        .flow-card {
            background:white; padding:18px; border-radius:14px;
            width:200px; box-shadow:0 6px 18px rgba(0,0,0,0.08);
            transition:0.2s;
        }
        .flow-card:hover { transform:translateY(-6px); }
        .flow-card .icon { font-size:28px; margin-bottom:10px; }
        .flow-card h3 { font-size:15px; margin-bottom:6px; color:#085041; }
        .flow-card p  { font-size:12px; color:#666; }
        .flow-arrow   { font-size:20px; color:#aaa; }

        /* Login portal cards */
        .portal-section {
            padding:50px 20px; max-width:1000px;
            margin:auto; text-align:center;
        }
        .portal-section h2 { font-size:24px; color:#085041; margin-bottom:30px; }
        .portal-grid {
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
            gap:20px;
        }
        .portal-card {
            background:white; padding:24px 16px; border-radius:14px;
            box-shadow:0 6px 18px rgba(0,0,0,0.08);
            border-top:4px solid #085041;
        }
        .portal-card .p-icon { font-size:32px; margin-bottom:10px; }
        .portal-card h3 { font-size:15px; color:#085041; margin-bottom:6px; }
        .portal-card p  { font-size:12px; color:#666; margin-bottom:16px; }
        .portal-card a  {
            display:inline-block; padding:9px 18px; border-radius:8px;
            text-decoration:none; font-size:13px; font-weight:600;
            background:#085041; color:white;
        }

        .footer {
            text-align:center; font-size:12px; color:#777; padding:20px;
        }

        @media(max-width:768px){
            .hero-container { text-align:center; justify-content:center; }
            .flow-arrow { display:none; }
            .navbar { padding:16px 20px; }
        }
    </style>
</head>
<body>

<!-- NAVBAR -->
<div class="navbar">
    <div class="nav-title">🌿 MaaSakhi</div>
    <div class="nav-links">
        <a href="/">Home</a>
        <a href="/login">Login</a>
        <a href="/admin/login">Admin</a>
    </div>
</div>

<!-- HERO -->
<div class="hero">
    <div class="hero-container">
        <div class="hero-text">
            <h1>AI-Powered Maternal Care on WhatsApp</h1>
            <p>
                Empowering pregnant women, ASHA workers, supervisors,
                and health officers with real-time monitoring,
                risk detection, and timely interventions.
            </p>
            <div class="hero-buttons">
                <a href="/login"       class="btn btn-primary">Login Portal</a>
                <a href="/admin/login" class="btn btn-secondary">Admin Panel</a>
            </div>
        </div>
        <div>
            <img src="/static/logo.png" alt="MaaSakhi">
        </div>
    </div>
</div>

<!-- TRUST BADGES -->
<div class="trust">
    <span>✔ WHO Guidelines</span>
    <span>✔ NHM Integrated</span>
    <span>✔ Real-time Alerts</span>
    <span>✔ Multi-language AI</span>
    <span>✔ Auto-Escalation</span>
    <span>✔ 5-Tier Hierarchy</span>
</div>

<!-- LOGIN PORTALS -->
<div class="portal-section">
    <h2>Login Portals</h2>
    <div class="portal-grid">
        <div class="portal-card" style="border-color:#085041">
            <div class="p-icon">👩</div>
            <h3>ASHA Worker</h3>
            <p>View your patients, respond to alerts, log visit outcomes</p>
            <a href="/login">Login</a>
        </div>
        <div class="portal-card" style="border-color:#0369A1">
            <div class="p-icon">👩‍💼</div>
            <h3>Supervisor (ANM)</h3>
            <p>Monitor your ASHA workers, handle escalated alerts</p>
            <a href="/login" style="background:#0369A1">Login</a>
        </div>
        <div class="portal-card" style="border-color:#B45309">
            <div class="p-icon">🏥</div>
            <h3>Block Medical Officer</h3>
            <p>Block-level oversight, critical escalation management</p>
            <a href="/login" style="background:#B45309">Login</a>
        </div>
        <div class="portal-card" style="border-color:#7C3AED">
            <div class="p-icon">🏛</div>
            <h3>District Admin (DHO)</h3>
            <p>Full district analytics, manage entire hierarchy</p>
            <a href="/admin/login" style="background:#7C3AED">Login</a>
        </div>
    </div>
</div>

<!-- HOW IT WORKS -->
<div class="flow">
    <h2>How MaaSakhi Works</h2>
    <p class="flow-subtext">
        A continuous care loop connecting patients, AI, ASHA workers,
        and health officers for early detection and timely intervention.
    </p>
    <div class="flow-grid">
        <div class="flow-card">
            <div class="icon">👩</div>
            <h3>Patient Reports</h3>
            <p>Women report symptoms via WhatsApp in their local language.</p>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-card">
            <div class="icon">🤖</div>
            <h3>AI Triage</h3>
            <p>Groq AI classifies risk as GREEN, AMBER, or RED instantly.</p>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-card">
            <div class="icon">🚨</div>
            <h3>ASHA Alerted</h3>
            <p>High-risk triggers instant WhatsApp alert with Maps link.</p>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-card">
            <div class="icon">⬆️</div>
            <h3>Auto-Escalation</h3>
            <p>No response in 2hrs → escalates to Supervisor → BMO → DHO.</p>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-card">
            <div class="icon">🏥</div>
            <h3>Timely Care</h3>
            <p>Patient receives attention before condition becomes critical.</p>
        </div>
    </div>
</div>

<!-- KEY FEATURES -->
<div class="features">
    <h2>Key Features</h2>
    <div class="feature-grid">
        <div class="card">📱 WhatsApp Bot — No App Needed</div>
        <div class="card">🚨 Real-time ASHA Alerts + Maps</div>
        <div class="card">⬆️ Auto-Escalation Hierarchy</div>
        <div class="card">🌍 100+ Indian Languages</div>
        <div class="card">🎤 Hindi Voice Notes (Whisper AI)</div>
        <div class="card">📊 Personalized Risk Scoring</div>
        <div class="card">🏥 ANC Checkup Reminders</div>
        <div class="card">💊 Medicine Schedule Alerts</div>
    </div>
</div>

<!-- FOOTER -->
<div class="footer">
    MaaSakhi • AI-driven Maternal Health Support System •
    Powered by WHO + NHM + FOGSI Guidelines
</div>

</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────
# HELPER — Recovery confirmation check
# ─────────────────────────────────────────────────────────────────

def handle_recovery_confirmation(sender, user, msg):
    """Returns BETTER, NOT_WELL or None."""
    recovery_keywords = [
        "i am better", "i am fine", "theek hoon", "theek hu",
        "better now", "feeling better", "mujhe theek", "ab theek",
        "recovered", "all good", "sahi hoon", "achha feel"
    ]
    not_well_keywords = [
        "still not", "abhi bhi", "nahi theek", "not better",
        "still sick", "still pain", "still not feeling well"
    ]
    msg_lower = msg.lower()
    if any(k in msg_lower for k in not_well_keywords):
        return "NOT_WELL"
    if any(k in msg_lower for k in recovery_keywords):
        return "BETTER"
    return None


# ─────────────────────────────────────────────────────────────────
# WHATSAPP BOT
# ─────────────────────────────────────────────────────────────────

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
                    "Maafi chahti hoon — main aapka voice note "
                    "samajh nahi payi. 🙏\n"
                    "Please type your symptom in text."
                )
                return str(response)
    except Exception as e:
        print(f"Voice handling error: {e}")

    # ── Load patient ──────────────────────────────────────────────
    user = get_patient(sender)
    if not user:
        user = {
            "phone":         sender,
            "name":          "",
            "week":          0,
            "step":          "welcome",
            "language":      "Hindi",
            "asha_id":       "default_asha",
            "supervisor_id": "",
            "bmo_id":        "",
            "village":       "",
            "address":       ""
        }
        save_patient(sender, "", 0, "welcome")

    # ─────────────────────────────────────────────────────────────
    # REGISTRATION FLOW
    # Steps: get_name → get_week → get_village → get_address → registered
    # ─────────────────────────────────────────────────────────────

    if incoming_msg.lower() in [
        "register", "register pregnancy",
        "hello", "hi", "start", "namaste"
    ]:
        if user["step"] == "registered":
            msg.body(
                f"🌸 Welcome back {user['name']}!\n\n"
                f"Aap week {user['week']} mein hain. "
                f"Main hamesha yahan hoon. 💚\n\n"
                f"Koi symptom feel ho toh batao, ya "
                f"'progress' type karo weekly update ke liye! 🌸"
            )
            return str(response)

        save_patient(sender, "", 0, "get_name")
        msg.body(
            "🌸 Namaste! Welcome to MaaSakhi — "
            "aapki maternal health companion!\n\n"
            "Pehle mujhe apna naam batao:\n"
            "Please tell me your name:"
        )

    elif user["step"] == "get_name":
        save_patient(sender, incoming_msg, 0, "get_week")
        msg.body(
            f"Namaste {incoming_msg}! 🙏\n\n"
            f"Aap kitne hafte ki pregnant hain?\n"
            f"How many weeks pregnant are you?\n\n"
            f"Sirf number bhejiye — Example: 26"
        )

    elif user["step"] == "get_week":
        try:
            week = int(incoming_msg)
            save_patient(sender, user["name"], week, "get_village")
            msg.body(
                f"Shukriya! 🌸\n\n"
                f"Aap kis gaon (village) mein rehti hain?\n"
                f"Which village do you live in?\n\n"
                f"Example: Rampur"
            )
        except ValueError:
            msg.body("Sirf number bhejiye. Example: 26")

    elif user["step"] == "get_village":
        village = incoming_msg.strip()

        # Auto-assign ASHA worker from this village
        asha = get_asha_by_village(village)
        asha_id       = asha["asha_id"]       if asha else "default_asha"
        supervisor_id = asha.get("supervisor_id", "") if asha else ""

        # Get supervisor's BMO
        bmo_id = ""
        if supervisor_id:
            try:
                from database import engine
                from sqlalchemy import text
                with engine.connect() as conn:
                    result = conn.execute(
                        text("""
                            SELECT bmo_id FROM asha_supervisors
                            WHERE supervisor_id = :id
                        """),
                        {"id": supervisor_id}
                    ).fetchone()
                    if result:
                        bmo_id = result.bmo_id or ""
            except Exception as e:
                print(f"BMO lookup error: {e}")

        save_patient(
            sender, user["name"], user["week"],
            "get_address", user["language"],
            asha_id, village, "",
            supervisor_id, bmo_id
        )
        msg.body(
            f"Shukriya {user['name']}! 🌸\n\n"
            f"Ab apna ghar ka address batao —\n"
            f"gali, mohalla ya koi pehchaan ki jagah.\n\n"
            f"Example: Near Govt School, Ward 4, Rampur\n\n"
            f"(Yeh ASHA worker ko emergency mein dhundhne mein "
            f"madad karega 🏥)"
        )

    elif user["step"] == "get_address":
        address = incoming_msg.strip()

        # Reload user to get saved village, asha_id, supervisor_id
        user = get_patient(sender)

        save_patient(
            sender,
            user["name"],
            user["week"],
            "registered",
            user["language"],
            user.get("asha_id",       "default_asha"),
            user.get("village",       ""),
            address,
            user.get("supervisor_id", ""),
            user.get("bmo_id",        "")
        )

        _, tip_msg, _ = analyze("tip", user["week"])
        msg.body(
            f"✅ Aap registered hain, {user['name']}!\n\n"
            f"📍 Village: {user.get('village', '')}\n"
            f"🏠 Address: {address}\n\n"
            f"Main aapke saath hoon 24/7. 💚\n\n"
            f"{tip_msg}\n\n"
            f"Koi bhi symptom feel ho — bas mujhe message karo. 🌸"
        )

    # ─────────────────────────────────────────────────────────────
    # SYMPTOM ANALYSIS (registered users)
    # ─────────────────────────────────────────────────────────────

    elif user["step"] == "registered":

        # ── Recovery confirmation ─────────────────────────────────
        recovery = handle_recovery_confirmation(sender, user, incoming_msg)

        if recovery == "BETTER":
            alert = get_alert_by_patient_phone(sender)
            if alert and alert["status"] == "Attended":
                update_alert_status(alert["id"], "Resolved")
                msg.body(
                    f"🌸 Bahut khushi hui, {user['name']}!\n\n"
                    f"✅ Aapki recovery confirm ho gayi.\n"
                    f"ASHA worker ko inform kar diya gaya hai.\n\n"
                    f"Apna khayal rakhein! 💚"
                )
            else:
                msg.body(
                    f"Khushi hui sunke {user['name']}! 🌸\n\n"
                    f"Agar koi aur symptom ho toh zaroor batana. 💚"
                )
            return str(response)

        if recovery == "NOT_WELL":
            alert = get_alert_by_patient_phone(sender)
            if alert:
                save_asha_alert_db(
                    sender,
                    user["name"],
                    user["week"],
                    "FOLLOW UP: Patient still not feeling well",
                    user.get("asha_id",       "default_asha"),
                    address       = user.get("address", ""),
                    village       = user.get("village", ""),
                    supervisor_id = user.get("supervisor_id", ""),
                    bmo_id        = user.get("bmo_id", "")
                )
            msg.body(
                f"🚨 ASHA worker ko dobara alert kar diya gaya hai, "
                f"{user['name']}.\n\n"
                f"Please nearest health centre zaroor jaayein. 🏥\n\n"
                f"Aap akeli nahi hain. 💚"
            )
            return str(response)

        # ── Update language ───────────────────────────────────────
        detected_lang = detect_language(incoming_msg)
        if detected_lang != user["language"]:
            save_patient(
                sender, user["name"], user["week"],
                "registered", detected_lang,
                user.get("asha_id",       "default_asha"),
                user.get("village",       ""),
                user.get("address",       ""),
                user.get("supervisor_id", ""),
                user.get("bmo_id",        "")
            )
            user["language"] = detected_lang

        # ── Progress tracker ──────────────────────────────────────
        if is_tracker_request(incoming_msg):
            reply = get_progress_update(
                user["week"],
                user["name"],
                sender,
                user["language"]
            )
            msg.body(reply)
            return str(response)

        # ── AI symptom analysis ───────────────────────────────────
        level, reply, alert_needed = analyze(incoming_msg, user["week"])

        # Save to health log
        save_symptom_log(sender, user["week"], incoming_msg, level)

        if level == "RED":
            # Build Google Maps link
            import urllib.parse
            location    = user.get("address") or user.get("village") or ""
            maps_link   = ""
            if location:
                encoded   = urllib.parse.quote(location + ", India")
                maps_link = (
                    f"https://www.google.com/maps/dir/"
                    f"?api=1&destination={encoded}"
                )

            full_reply = (
                f"{reply}\n\n"
                f"Aapki ASHA worker ko alert kar diya gaya hai.\n"
                f"Please go to your nearest health centre "
                f"immediately. 🏥"
            )

            # Save alert with full hierarchy IDs + address + maps
            save_asha_alert_db(
                sender,
                user["name"],
                user["week"],
                incoming_msg,
                user.get("asha_id",       "default_asha"),
                address       = user.get("address", ""),
                village       = user.get("village", ""),
                maps_link     = maps_link,
                supervisor_id = user.get("supervisor_id", ""),
                bmo_id        = user.get("bmo_id",        "")
            )

            # Send WhatsApp alert to ASHA worker
            save_alert(
                user["name"],
                user["week"],
                incoming_msg,
                sender,
                user.get("asha_id", "default_asha"),
                address   = user.get("address", ""),
                village   = user.get("village", "")
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
            full_reply = f"{reply}\n\nKoi symptom feel ho toh batao! 🌸"

        else:
            full_reply = (
                f"{reply}\n\n"
                f"Paani piyen, rest karein, aur iron ki "
                f"goli lena mat bhoolein! 💚"
            )

        msg.body(full_reply)

    else:
        msg.body(
            "Namaste! 'Register' ya 'Hello' type karke shuru karein.\n"
            "Type 'Register' to get started with MaaSakhi 🌸"
        )

    return str(response)


# ─────────────────────────────────────────────────────────────────
# UNIFIED LOGIN — one login for all roles
# Detects role automatically and redirects to correct dashboard
# ─────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()

        # Normalise phone number
        clean = phone.replace("+91", "").replace(" ", "").replace("-", "")
        if len(clean) == 10 and clean.isdigit():
            wa_phone    = "whatsapp:+91" + clean
            plain_phone = "+91" + clean
        else:
            wa_phone    = phone
            plain_phone = phone

        # Try all roles in priority order
        user = unified_login(wa_phone) or unified_login(plain_phone)

        if user:
            role = user.get("role")
            if role == "asha":
                return redirect(f"/dashboard/{user['asha_id']}")
            elif role == "supervisor":
                return redirect(f"/supervisor/{user['supervisor_id']}")
            elif role == "bmo":
                return redirect(f"/bmo/{user['bmo_id']}")
        else:
            error = "❌ Phone number not found. Please contact your admin."

    login_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MaaSakhi Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{
                font-family:'Poppins',sans-serif;
                background:linear-gradient(135deg,#085041,#0a6b52);
                min-height:100vh;
                display:flex; justify-content:center; align-items:center;
            }}
            .box {{
                background:white; padding:36px 32px; border-radius:16px;
                box-shadow:0 20px 60px rgba(0,0,0,0.2);
                width:90%; max-width:380px; text-align:center;
            }}
            .logo {{ font-size:36px; margin-bottom:6px; }}
            h2 {{ font-size:20px; color:#085041; }}
            p  {{ font-size:13px; color:#666; margin-top:4px; }}
            .roles {{
                display:grid; grid-template-columns:1fr 1fr;
                gap:8px; margin:20px 0 16px;
            }}
            .role-badge {{
                padding:8px; border-radius:8px; font-size:11px;
                font-weight:600;
            }}
            input {{
                width:100%; padding:13px; margin-top:4px;
                border-radius:8px; border:1.5px solid #e5e7eb;
                font-family:'Poppins',sans-serif; font-size:14px;
            }}
            input:focus {{ outline:none; border-color:#085041; }}
            button {{
                margin-top:16px; width:100%; padding:13px;
                background:#085041; color:white; border:none;
                border-radius:8px; font-size:15px;
                font-weight:600; cursor:pointer;
                font-family:'Poppins',sans-serif;
            }}
            button:hover {{ background:#0a6b52; }}
            .error {{
                background:#fef2f2; color:#dc2626; padding:10px;
                border-radius:8px; font-size:13px; margin-top:12px;
            }}
            .back {{
                display:block; margin-top:16px;
                font-size:12px; color:#085041; text-decoration:none;
            }}
            .admin-link {{
                display:block; margin-top:10px;
                font-size:12px; color:#7C3AED; text-decoration:none;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <div class="logo">🌿</div>
            <h2>MaaSakhi Login</h2>
            <p>One login for all health workers</p>

            <div class="roles">
                <div class="role-badge" style="background:#e6f4f1;color:#085041">
                    👩 ASHA Worker
                </div>
                <div class="role-badge" style="background:#e0f0ff;color:#0369A1">
                    👩‍💼 Supervisor
                </div>
                <div class="role-badge" style="background:#fff3e0;color:#B45309">
                    🏥 BMO
                </div>
                <div class="role-badge" style="background:#f3e8ff;color:#7C3AED">
                    🏛 DHO → Admin
                </div>
            </div>

            <form method="POST">
                <input
                    name="phone"
                    placeholder="Enter your 10-digit mobile number"
                    pattern="[0-9+\\s-]{{10,14}}"
                    required
                />
                {"<div class='error'>" + error + "</div>" if error else ""}
                <button type="submit">Login →</button>
            </form>

            <a href="/"           class="back">← Back to Home</a>
            <a href="/admin/login" class="admin-link">🔐 District Admin Login</a>
        </div>
    </body>
    </html>
    """
    return login_html


# ─────────────────────────────────────────────────────────────────
# ASHA WORKER DASHBOARD
# ─────────────────────────────────────────────────────────────────

@app.route("/dashboard/<asha_id>")
def dashboard(asha_id):
    patients  = get_all_patients(asha_id)
    alerts    = get_all_asha_alerts(asha_id)
    high_risk = len([a for a in alerts if a["status"] != "Resolved"])
    safe      = max(len(patients) - high_risk, 0)
    return render_dashboard(patients, high_risk, len(patients), safe, asha_id)


@app.route("/dashboard/<asha_id>/attend/<alert_id>", methods=["POST"])
def mark_attended(asha_id, alert_id):
    from database import engine
    from sqlalchemy import text

    update_alert_status(int(alert_id), "Attended")

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM asha_alerts WHERE id = :id"),
                {"id": int(alert_id)}
            ).fetchone()

            if result:
                asha = conn.execute(
                    text("SELECT name FROM asha_workers WHERE asha_id = :id"),
                    {"id": asha_id}
                ).fetchone()
                asha_name = asha.name if asha else "Aapki ASHA worker"

                from twilio.rest import Client
                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                client.messages.create(
                    from_="whatsapp:+14155238886",
                    to=result.phone,
                    body=(
                        f"🌸 Namaste {result.name}!\n\n"
                        f"*{asha_name}* ne aapka case attend kar liya hai. 💚\n\n"
                        f"Kya aap ab theek feel kar rahi hain?\n\n"
                        f"Reply karein:\n"
                        f"✅ *'I am better'* — agar theek hain\n"
                        f"⚠️ *'Still not feeling well'* — agar takleef hai"
                    )
                )
    except Exception as e:
        print(f"Attend alert error: {e}")

    return redirect(f"/dashboard/{asha_id}")


@app.route("/dashboard/<asha_id>/log-visit/<alert_id>", methods=["POST"])
def log_visit(asha_id, alert_id):
    """ASHA logs what happened during her visit."""
    outcome     = request.form.get("outcome",    "stable")
    notes       = request.form.get("notes",      "")
    referred_to = request.form.get("referred_to","")

    alert = get_alert_by_id(int(alert_id))
    if alert:
        save_asha_visit(
            alert_id    = int(alert_id),
            phone       = alert["phone"],
            patient_name= alert["name"],
            asha_id     = asha_id,
            outcome     = outcome,
            notes       = notes,
            referred_to = referred_to
        )
        # If referred or emergency — mark as resolved
        if outcome in ["referred_phc", "referred_hospital",
                       "called_108"]:
            update_alert_status(int(alert_id), "Resolved",
                                notes=f"Referred: {referred_to}")
        else:
            update_alert_status(int(alert_id), "Attended")

    return redirect(f"/dashboard/{asha_id}")


# ─────────────────────────────────────────────────────────────────
# SUPERVISOR DASHBOARD
# ─────────────────────────────────────────────────────────────────

@app.route("/supervisor/<supervisor_id>")
def supervisor_dashboard(supervisor_id):
    stats   = get_supervisor_stats(supervisor_id)
    ashas   = get_supervisor_ashas(supervisor_id)
    alerts  = get_supervisor_alerts(supervisor_id)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Supervisor Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ font-family:Arial,sans-serif; background:#f0f4ff; }}
            .header {{
                background:#0369A1; color:white;
                padding:20px 24px;
            }}
            .header h1 {{ font-size:20px; }}
            .header p  {{ font-size:13px; opacity:0.85; margin-top:4px; }}
            .stats {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
                gap:12px; padding:20px;
            }}
            .stat {{
                background:white; border-radius:12px; padding:16px;
                text-align:center; border:1px solid #e0eaff;
            }}
            .stat-n {{ font-size:30px; font-weight:bold; }}
            .stat-l {{ font-size:12px; color:#888; margin-top:4px; }}
            .section {{
                padding:0 20px 12px;
                font-size:12px; font-weight:bold;
                color:#0369A1; text-transform:uppercase;
                letter-spacing:.05em; margin-top:10px;
            }}
            .alert-card {{
                margin:0 20px 10px; background:white;
                border-radius:12px; padding:14px;
                border-left:4px solid #ef4444;
            }}
            .asha-card {{
                margin:0 20px 8px; background:white;
                border-radius:10px; padding:14px;
                display:flex; justify-content:space-between;
                align-items:center; border:1px solid #e0eaff;
            }}
            .badge {{
                display:inline-block; padding:2px 10px;
                border-radius:20px; font-size:11px; font-weight:bold;
            }}
            .red  {{ background:#fef2f2; color:#dc2626; }}
            .green{{ background:#f0fdf4; color:#16a34a; }}
            .blue {{ background:#eff6ff; color:#1d4ed8; }}
            .btn-escalate {{
                background:#dc2626; color:white; border:none;
                padding:6px 14px; border-radius:6px;
                font-size:12px; cursor:pointer;
            }}
            .empty {{
                text-align:center; padding:30px; color:#aaa;
                font-size:14px;
            }}
            .footer {{
                text-align:center; font-size:12px;
                color:#aaa; padding:20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>👩‍💼 Supervisor Dashboard</h1>
            <p>Auto-refreshes every 30 seconds • Block Level View</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-n" style="color:#0369A1">
                    {stats.get('total_ashas', 0)}
                </div>
                <div class="stat-l">ASHA Workers</div>
            </div>
            <div class="stat">
                <div class="stat-n" style="color:#085041">
                    {stats.get('total_patients', 0)}
                </div>
                <div class="stat-l">Total Patients</div>
            </div>
            <div class="stat">
                <div class="stat-n" style="color:#ef4444">
                    {stats.get('pending_alerts', 0)}
                </div>
                <div class="stat-l">Pending Alerts</div>
            </div>
            <div class="stat">
                <div class="stat-n" style="color:#f59e0b">
                    {stats.get('escalated_to_me', 0)}
                </div>
                <div class="stat-l">Escalated to Me</div>
            </div>
        </div>

        <p class="section">⚠️ Alerts Across My ASHA Workers</p>
    """

    if alerts:
        for a in alerts:
            status_class = "red" if a["status"] == "Pending" else "blue"
            maps_btn = (
                f'<a href="{a["maps_link"]}" target="_blank" '
                f'style="font-size:12px;color:#0369A1">📌 Navigate</a>'
                if a.get("maps_link") else ""
            )
            html += f"""
            <div class="alert-card">
                <div style="display:flex;justify-content:space-between;
                            align-items:center">
                    <strong>{a['name']}</strong>
                    <span class="badge {status_class}">{a['status']}</span>
                </div>
                <div style="font-size:13px;color:#555;margin-top:4px">
                    Week {a['week']} • {a['symptom'][:60]}
                </div>
                <div style="font-size:12px;color:#888;margin-top:4px">
                    ASHA: {a.get('asha_name','—')} •
                    Village: {a.get('village','—')} •
                    {a['time']}
                </div>
                <div style="margin-top:6px;display:flex;gap:8px">
                    {maps_btn}
                    {'<form method="POST" action="/supervisor/'
                     + supervisor_id + '/escalate/' + str(a['id'])
                     + '" style="display:inline">'
                     '<button class="btn-escalate">⬆ Escalate to BMO'
                     '</button></form>'
                     if a['status'] == 'Pending' and a.get('level',0) < 2
                     else ''}
                </div>
            </div>
            """
    else:
        html += "<div class='empty'>✅ No active alerts</div>"

    html += "<p class='section' style='margin-top:12px'>👩 My ASHA Workers</p>"

    for a in ashas:
        status = "🟢 Active" if a["is_active"] else "🔴 Inactive"
        html += f"""
        <div class="asha-card">
            <div>
                <div style="font-weight:500">{a['name']}</div>
                <div style="font-size:12px;color:#666">
                    {a['village']} •
                    {a['patient_count']} patients •
                    {a['pending_alerts']} pending
                </div>
            </div>
            <div>
                <span class="badge {'green' if a['is_active'] else 'red'}">
                    {status}
                </span>
            </div>
        </div>
        """

    html += f"""
        <div class="footer">
            MaaSakhi Supervisor Dashboard •
            <a href="/login">← Logout</a>
        </div>
        <script>setTimeout(()=>location.reload(), 30000);</script>
    </body>
    </html>
    """
    return html


@app.route("/supervisor/<supervisor_id>/escalate/<alert_id>",
           methods=["POST"])
def supervisor_escalate(supervisor_id, alert_id):
    """Supervisor manually escalates an alert to BMO."""
    from escalation import trigger_manual_escalation
    trigger_manual_escalation(int(alert_id))
    return redirect(f"/supervisor/{supervisor_id}")


# ─────────────────────────────────────────────────────────────────
# BMO DASHBOARD
# ─────────────────────────────────────────────────────────────────

@app.route("/bmo/<bmo_id>")
def bmo_dashboard(bmo_id):
    stats  = get_bmo_stats(bmo_id)
    alerts = get_bmo_alerts(bmo_id)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BMO Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ font-family:Arial,sans-serif; background:#fff8f0; }}
            .header {{
                background:#B45309; color:white; padding:20px 24px;
            }}
            .header h1 {{ font-size:20px; }}
            .header p  {{ font-size:13px; opacity:0.85; margin-top:4px; }}
            .stats {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
                gap:12px; padding:20px;
            }}
            .stat {{
                background:white; border-radius:12px; padding:16px;
                text-align:center; border:1px solid #fde8c8;
            }}
            .stat-n {{ font-size:30px; font-weight:bold; }}
            .stat-l {{ font-size:12px; color:#888; margin-top:4px; }}
            .section {{
                padding:0 20px 12px; font-size:12px;
                font-weight:bold; color:#B45309;
                text-transform:uppercase; letter-spacing:.05em;
                margin-top:10px;
            }}
            .alert-card {{
                margin:0 20px 10px; background:white;
                border-radius:12px; padding:14px;
                border-left:4px solid #dc2626;
            }}
            .btn-escalate {{
                background:#7C3AED; color:white; border:none;
                padding:6px 14px; border-radius:6px;
                font-size:12px; cursor:pointer;
            }}
            .empty {{
                text-align:center; padding:30px;
                color:#aaa; font-size:14px;
            }}
            .footer {{
                text-align:center; font-size:12px;
                color:#aaa; padding:20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏥 Block Medical Officer Dashboard</h1>
            <p>Critical escalations requiring block-level intervention</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-n" style="color:#0369A1">
                    {stats.get('total_supervisors', 0)}
                </div>
                <div class="stat-l">Supervisors</div>
            </div>
            <div class="stat">
                <div class="stat-n" style="color:#085041">
                    {stats.get('total_ashas', 0)}
                </div>
                <div class="stat-l">ASHA Workers</div>
            </div>
            <div class="stat">
                <div class="stat-n" style="color:#085041">
                    {stats.get('total_patients', 0)}
                </div>
                <div class="stat-l">Patients</div>
            </div>
            <div class="stat">
                <div class="stat-n" style="color:#dc2626">
                    {stats.get('escalated_alerts', 0)}
                </div>
                <div class="stat-l">Escalated Alerts</div>
            </div>
        </div>

        <p class="section">🚨 Escalated Alerts — Requires Your Attention</p>
    """

    if alerts:
        for a in alerts:
            maps_btn = (
                f'<a href="{a["maps_link"]}" target="_blank" '
                f'style="font-size:12px;color:#B45309">📌 Navigate</a>'
                if a.get("maps_link") else ""
            )
            html += f"""
            <div class="alert-card">
                <div style="display:flex;justify-content:space-between">
                    <strong>🚨 {a['name']}</strong>
                    <span style="font-size:12px;color:#dc2626;font-weight:bold">
                        ESCALATED
                    </span>
                </div>
                <div style="font-size:13px;color:#555;margin-top:4px">
                    Week {a['week']} • {a['symptom'][:70]}
                </div>
                <div style="font-size:12px;color:#888;margin-top:4px">
                    ASHA: {a.get('asha_name','—')} •
                    Village: {a.get('village','—')} •
                    Address: {a.get('address','—')}
                </div>
                <div style="font-size:12px;color:#888">
                    📞 Patient: {a['phone']} • {a['time']}
                </div>
                <div style="margin-top:8px;display:flex;gap:8px">
                    {maps_btn}
                    <form method="POST"
                          action="/bmo/{bmo_id}/resolve/{a['id']}"
                          style="display:inline">
                        <button style="background:#085041;color:white;
                                       border:none;padding:6px 14px;
                                       border-radius:6px;font-size:12px;
                                       cursor:pointer">
                            ✅ Mark Resolved
                        </button>
                    </form>
                    <form method="POST"
                          action="/bmo/{bmo_id}/escalate/{a['id']}"
                          style="display:inline">
                        <button class="btn-escalate">
                            ⬆ Escalate to DHO
                        </button>
                    </form>
                </div>
            </div>
            """
    else:
        html += "<div class='empty'>✅ No escalated alerts</div>"

    html += f"""
        <div class="footer">
            MaaSakhi BMO Dashboard •
            <a href="/login">← Logout</a>
        </div>
        <script>setTimeout(()=>location.reload(), 30000);</script>
    </body>
    </html>
    """
    return html


@app.route("/bmo/<bmo_id>/escalate/<alert_id>", methods=["POST"])
def bmo_escalate(bmo_id, alert_id):
    """BMO manually escalates to DHO."""
    from escalation import trigger_manual_escalation
    trigger_manual_escalation(int(alert_id))
    return redirect(f"/bmo/{bmo_id}")


@app.route("/bmo/<bmo_id>/resolve/<alert_id>", methods=["POST"])
def bmo_resolve(bmo_id, alert_id):
    update_alert_status(int(alert_id), "Resolved", notes="Resolved by BMO")
    return redirect(f"/bmo/{bmo_id}")


# ─────────────────────────────────────────────────────────────────
# ADMIN / DHO ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin    = verify_admin(username, password)
        if admin:
            session["admin"] = admin
            return redirect("/admin")
        return render_admin_login(error="Invalid username or password")
    return render_admin_login()


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")


@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin/login")
    tab = request.args.get("tab", "asha")
    return render_admin_panel(
        admin_name=session["admin"]["name"],
        tab=tab
    )


@app.route("/admin/add-asha", methods=["POST"])
def admin_add_asha():
    if "admin" not in session:
        return redirect("/admin/login")
    success = add_asha_worker(
        asha_id       = request.form.get("asha_id",       "").strip(),
        name          = request.form.get("name",          "").strip(),
        phone         = request.form.get("phone",         "").strip(),
        village       = request.form.get("village",       "").strip(),
        district      = request.form.get("district",      "").strip(),
        block_name    = request.form.get("block_name",    "").strip(),
        supervisor_id = request.form.get("supervisor_id", "").strip()
    )
    return render_admin_panel(
        admin_name=session["admin"]["name"],
        tab="asha",
        message="ASHA worker added!" if success else "Failed.",
        success=success
    )


@app.route("/admin/add-supervisor", methods=["POST"])
def admin_add_supervisor():
    if "admin" not in session:
        return redirect("/admin/login")
    success = add_asha_supervisor(
        supervisor_id = request.form.get("supervisor_id", "").strip(),
        name          = request.form.get("name",          "").strip(),
        phone         = request.form.get("phone",         "").strip(),
        block_name    = request.form.get("block_name",    "").strip(),
        district      = request.form.get("district",      "").strip(),
        bmo_id        = request.form.get("bmo_id",        "").strip()
    )
    return render_admin_panel(
        admin_name=session["admin"]["name"],
        tab="supervisors",
        message="Supervisor added!" if success else "Failed.",
        success=success
    )


@app.route("/admin/add-bmo", methods=["POST"])
def admin_add_bmo():
    if "admin" not in session:
        return redirect("/admin/login")
    success = add_block_officer(
        bmo_id     = request.form.get("bmo_id",     "").strip(),
        name       = request.form.get("name",       "").strip(),
        phone      = request.form.get("phone",      "").strip(),
        block_name = request.form.get("block_name", "").strip(),
        district   = request.form.get("district",   "").strip()
    )
    return render_admin_panel(
        admin_name=session["admin"]["name"],
        tab="bmo",
        message="BMO added!" if success else "Failed.",
        success=success
    )


@app.route("/admin/toggle-asha", methods=["POST"])
def admin_toggle_asha():
    if "admin" not in session:
        return redirect("/admin/login")
    toggle_asha_status(request.form.get("asha_id"))
    return redirect("/admin?tab=asha")


@app.route("/admin/delete-asha", methods=["POST"])
def admin_delete_asha():
    if "admin" not in session:
        return redirect("/admin/login")
    delete_asha_worker(request.form.get("asha_id"))
    return redirect("/admin?tab=asha")


# ─────────────────────────────────────────────────────────────────
# HOMEPAGE
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template_string(HOMEPAGE_HTML)


# ─────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)