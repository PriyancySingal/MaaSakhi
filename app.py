# ─────────────────────────────────────────────────────────────────
# MaaSakhi — Main Application
# WhatsApp Maternal Health Bot for Rural India
# Full 4-Month Feature Set:
#   Month 1 — Visit logging, schemes, address + Maps
#   Month 2 — Supervisor layer, escalation, performance
#   Month 3 — Analytics, ANC records, NHM export
#   Month 4 — Postpartum, child health, immunization, reminders
# ─────────────────────────────────────────────────────────────────

import os
from datetime import datetime
from flask import (
    Flask, request, render_template_string,
    session, redirect, jsonify, Response
)
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

from config   import PORT, DEBUG, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from voice    import transcribe_voice_note
from analyzer import analyze, detect_language_from_text as detect_language
from alerts   import save_alert
from dashboard import render_dashboard
from tracker  import get_progress_update, is_tracker_request
from admin    import render_admin_login, render_admin_panel
from escalation import start_escalation_engine

from database import (
    # Core
    init_db, engine,
    # Patient
    get_patient, save_patient,
    get_all_patients, get_all_patients_admin,
    save_symptom_log, update_patient_status,
    # ASHA Worker
    get_asha_by_village, get_asha_by_phone,
    get_all_asha_workers,
    add_asha_worker, toggle_asha_status, delete_asha_worker,
    get_asha_stats, get_asha_performance,
    # Supervisor
    verify_supervisor,
    add_asha_supervisor, get_all_supervisors,
    get_supervisor_stats, get_supervisor_ashas,
    get_supervisor_alerts, get_patients_by_supervisor,
    toggle_supervisor_status, delete_supervisor,
    # BMO
    verify_bmo,
    add_block_officer, get_all_block_officers,
    get_bmo_stats, get_bmo_alerts,
    get_patients_by_bmo,
    toggle_bmo_status, delete_block_officer,
    # Admin / DHO
    verify_admin, get_district_stats,
    get_all_alerts_admin, get_district_trends,
    get_village_risk_scores,
    # Alerts
    save_asha_alert_db, get_all_asha_alerts,
    get_alert_count_db, update_alert_status,
    get_alert_by_patient_phone, get_alert_by_id,
    escalate_alert, log_escalation,
    # Visits
    save_asha_visit, get_asha_visits,
    # ANC
    save_anc_record, get_anc_records,
    # Schemes
    save_scheme_delivery, get_scheme_deliveries,
    # Postpartum + Child (Month 4)
    save_delivery_record, get_delivery_record,
    save_child, get_children,
    save_growth_log, get_growth_logs,
    save_immunization_record, get_immunization_records,
    get_postpartum_patients_due,
    # Unified login
    unified_login,
)

# ─────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "maasakhi2026secret")

init_db()
start_escalation_engine()

TWILIO_WA_FROM = "whatsapp:+14155238886"

def twilio_client():
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp(to, body):
    """Fire-and-forget WhatsApp message; silently swallows errors."""
    try:
        twilio_client().messages.create(
            from_=TWILIO_WA_FROM,
            to=to,
            body=body
        )
    except Exception as e:
        print(f"WhatsApp send error → {to}: {e}")


# ─────────────────────────────────────────────────────────────────
# HOMEPAGE
# ─────────────────────────────────────────────────────────────────
HOMEPAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MaaSakhi | Maternal Care AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Poppins',sans-serif;background:#f8fafc;color:#1e293b;overflow-x:hidden}
        
        /* Navigation */
        .navbar{display:flex;justify-content:space-between;align-items:center;
                padding:12px 8%;background:white;box-shadow:0 2px 10px rgba(0,0,0,0.05);position:sticky;top:0;z-index:100}
        
        /* Logo Styling */
        .nav-logo-container{display:flex;align-items:center;text-decoration:none}
        .logo-img{height:45px; width:auto; display:block; object-fit:contain}
        
        .nav-links a{margin-left:25px;text-decoration:none;color:#475569;font-size:14px;font-weight:500;transition:0.3s}
        .nav-links a:hover{color:#085041}

        /* Hero */
        .hero{background:linear-gradient(135deg,#085041,#0a6b52);color:white;padding:100px 8%}
        .hero-container{max-width:1200px;margin:auto}
        .hero-text h1{font-size:42px;font-weight:600;line-height:1.2}
        .hero-text p{margin-top:20px;font-size:18px;opacity:0.9;max-width:600px}
        .hero-buttons{margin-top:30px}
        .btn{display:inline-block;padding:14px 28px;border-radius:50px;
             text-decoration:none;font-size:15px;font-weight:600;transition:0.3s;margin-right:12px}
        .btn-primary{background:white;color:#085041}
        .btn-secondary{background:rgba(255,255,255,0.1);color:white;border:1px solid rgba(255,255,255,0.3)}
        .btn:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,0.15)}

        .trust{text-align:center;padding:30px;background:#fff;font-size:13px;color:#64748b;border-bottom:1px solid #e2e8f0}
        .trust span{margin:0 15px;display:inline-block}

        /* Portals */
        .portal-section{padding:80px 8%;max-width:1300px;margin:auto}
        .section-title{text-align:center;margin-bottom:50px}
        .section-title h2{font-size:28px;color:#085041}
        .portal-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:25px}
        .portal-card{background:white;padding:35px 25px;border-radius:20px;text-align:center;
                     box-shadow:0 10px 25px rgba(0,0,0,0.04);border-top:5px solid #085041;transition:0.3s}
        .portal-card:hover{transform:translateY(-5px)}
        .portal-card h3{font-size:17px;margin:15px 0 10px;color:#085041}
        .portal-card p{font-size:13px;color:#64748b;margin-bottom:20px;height:40px}
        .portal-card a{display:block;padding:10px;border-radius:8px;text-decoration:none;
                       background:#085041;color:white;font-size:14px;font-weight:600}

        /* How it Works */
        .how-it-works{background:#f1f5f9;padding:80px 8%}
        .flow-container{display:flex;justify-content:space-between;max-width:1100px;margin:50px auto 0;position:relative}
        .flow-step{flex:1;text-align:center;padding:0 15px;position:relative;z-index:2}
        .step-circle{width:50px;height:50px;background:#085041;color:white;border-radius:50%;
                     display:flex;align-items:center;justify-content:center;margin:0 auto 20px;
                     font-weight:600;box-shadow:0 0 0 8px rgba(8,80,65,0.1)}
        .flow-step h3{font-size:15px;margin-bottom:8px;color:#085041}
        .flow-step p{font-size:12px;color:#64748b}
        .flow-line{position:absolute;top:25px;left:10%;right:10%;height:2px;background:#cbd5e1;z-index:1}

        /* Key Features Slider */
        .features-slider-section{padding:80px 0;background:white;overflow:hidden}
        .slider-track{display:flex;gap:20px;padding:20px 0;width:max-content;animation:scroll 40s linear infinite}
        .slider-track:hover{animation-play-state:paused}
        .feature-item{width:280px;background:#f8faf9;padding:25px;border-radius:16px;
                      border:1px solid #e2e8f0;flex-shrink:0;transition:0.3s}
        .feature-item:hover{border-color:#085041;background:white;box-shadow:0 10px 20px rgba(0,0,0,0.05)}
        .feature-item b{display:block;margin-bottom:8px;color:#085041;font-size:15px}
        .feature-item p{font-size:13px;color:#64748b}

        @keyframes scroll {
            0% { transform: translateX(0); }
            100% { transform: translateX(calc(-280px * 6 - 120px)); }
        }

        .footer{text-align:center;padding:40px;background:#085041;color:rgba(255,255,255,0.7);font-size:12px}

        @media(max-width:768px){
            .flow-container{flex-direction:column;gap:30px}
            .flow-line{display:none}
            .hero-text h1{font-size:32px}
            .navbar{padding:12px 5%}
        }
    </style>
</head>
<body>

<div class="navbar">
    <a href="/" class="nav-logo-container">
        <img src="logo.png" alt="MaaSakhi Logo" class="logo-img">
    </a>
    <div class="nav-links">
        <a href="/">Overview</a>
        <a href="/login">Login</a>
        <a href="/admin/login" style="color:#085041;font-weight:600">Admin Portal</a>
    </div>
</div>

<div class="hero">
    <div class="hero-container">
        <div class="hero-text">
            <h1>AI-Powered Maternal Care <br>Directly on WhatsApp</h1>
            <p>A mission-critical bridge between pregnant women and life-saving interventions using real-time AI triage and automated escalation.</p>
            <div class="hero-buttons">
                <a href="/login" class="btn btn-primary">Health Worker Login</a>
                <a href="/admin/login" class="btn btn-secondary">System Admin</a>
            </div>
        </div>
    </div>
</div>

<div class="trust">
    <span>🛡 WHO Protocols</span><span>📋 NHM Integration</span><span>🌍 100+ Languages</span><span>🚨 Zero Delay Logic</span>
</div>

<div class="how-it-works">
    <div class="section-title">
        <h2>How MaaSakhi Protects</h2>
        <p style="color:#64748b;margin-top:10px">A seamless communication loop from village to district hospital.</p>
    </div>
    <div class="flow-container">
        <div class="flow-line"></div>
        <div class="flow-step">
            <div class="step-circle">1</div>
            <h3>Reporting</h3>
            <p>Patient sends symptoms via WhatsApp (Voice/Text).</p>
        </div>
        <div class="flow-step">
            <div class="step-circle">2</div>
            <h3>AI Analysis</h3>
            <p>Groq AI triages risk levels instantly.</p>
        </div>
        <div class="flow-step">
            <div class="step-circle">3</div>
            <h3>Alerting</h3>
            <p>ASHA receives priority alert with Maps location.</p>
        </div>
        <div class="flow-step">
            <div class="step-circle">4</div>
            <h3>Escalation</h3>
            <p>MO/DHO notified if no response within 2 hours.</p>
        </div>
        <div class="flow-step">
            <div class="step-circle">5</div>
            <h3>Resolution</h3>
            <p>Follow-up logged and risk status updated.</p>
        </div>
    </div>
</div>

<div class="portal-section">
    <div class="section-title"><h2>Specialized Access Portals</h2></div>
    <div class="portal-grid">
        <div class="portal-card" style="border-color:#085041">
            <div style="font-size:30px">👩‍⚕️</div>
            <h3>ASHA Worker</h3>
            <p>Manage village patients and active alerts.</p>
            <a href="/login">Access Portal</a>
        </div>
        <div class="portal-card" style="border-color:#0369a1">
            <div style="font-size:30px">📋</div>
            <h3>Supervisor</h3>
            <p>Monitor ASHA performance and Amber risks.</p>
            <a href="/login" style="background:#0369a1">Access Portal</a>
        </div>
        <div class="portal-card" style="border-color:#b45309">
            <div style="font-size:30px">🏥</div>
            <h3>Medical Officer</h3>
            <p>Clinical oversight for block-level emergencies.</p>
            <a href="/login" style="background:#b45309">Access Portal</a>
        </div>
        <div class="portal-card" style="border-color:#7c3aed">
            <div style="font-size:30px">📊</div>
            <h3>Health Admin</h3>
            <p>District-wide analytics and system health.</p>
            <a href="/admin/login" style="background:#7c3aed">Access Portal</a>
        </div>
    </div>
</div>

<div class="features-slider-section">
    <div class="section-title"><h2>Key Capabilities</h2></div>
    <div class="slider-track">
        <div class="feature-item"><b>📱 WhatsApp Native</b><p>No app installation required for patients or workers.</p></div>
        <div class="feature-item"><b>🌍 Multilingual AI</b><p>Supports 100+ Indian languages and regional dialects.</p></div>
        <div class="feature-item"><b>🚨 Smart Escalation</b><p>Hierarchical alerts (ASHA → ANM → BMO → DHO).</p></div>
        <div class="feature-item"><b>🎙️ Voice Intelligence</b><p>Hindi/Regional voice note processing via Whisper AI.</p></div>
        <div class="feature-item"><b>📍 Live Tracking</b><p>Google Maps integration for emergency patient location.</p></div>
        <div class="feature-item"><b>📈 Data Analytics</b><p>Real-time district-level maternal health heatmaps.</p></div>
        <div class="feature-item"><b>📱 WhatsApp Native</b><p>No app installation required for patients or workers.</p></div>
        <div class="feature-item"><b>🌍 Multilingual AI</b><p>Supports 100+ Indian languages and regional dialects.</p></div>
        <div class="feature-item"><b>🚨 Smart Escalation</b><p>Hierarchical alerts (ASHA → ANM → BMO → DHO).</p></div>
    </div>
</div>

<div class="footer">
    <p>MaaSakhi Intelligence © 2026 • Powered by WHO + NHM + FOGSI Clinical Guidelines</p>
</div>

</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def handle_recovery_confirmation(msg):
    """Returns 'BETTER', 'NOT_WELL', or None."""
    m = msg.lower()
    if any(k in m for k in [
        "still not", "abhi bhi", "nahi theek", "not better",
        "still sick", "still pain"
    ]):
        return "NOT_WELL"
    if any(k in m for k in [
        "i am better", "i am fine", "theek hoon", "theek hu",
        "better now", "feeling better", "recovered", "all good",
        "sahi hoon", "mujhe theek", "ab theek"
    ]):
        return "BETTER"
    return None


def _bmo_id_from_supervisor(supervisor_id):
    """Look up the bmo_id for a given supervisor."""
    if not supervisor_id or not engine:
        return ""
    try:
        from sqlalchemy import text as sqlt
        with engine.connect() as conn:
            row = conn.execute(
                sqlt("SELECT bmo_id FROM asha_supervisors WHERE supervisor_id = :id"),
                {"id": supervisor_id}
            ).fetchone()
            return (row.bmo_id or "") if row else ""
    except Exception as e:
        print(f"BMO lookup error: {e}")
        return ""


def _maps_link(address, village):
    import urllib.parse
    location = address or village or ""
    if not location:
        return ""
    encoded = urllib.parse.quote(location + ", India")
    return f"https://www.google.com/maps/dir/?api=1&destination={encoded}"


def is_visual_symptom(text):
    text = text.lower()
    keywords = [
        "rash", "allergy", "itch", "itching", "skin",
        "burn", "cut", "wound", "injury", "swelling",
        "redness", "infection", "pimple", "blister",
        "daane", "khujli", "jalan", "sujan", "ghav"
    ]
    return any(k in text for k in keywords)



# ─────────────────────────────────────────────────────────────────
# WHATSAPP BOT
# ─────────────────────────────────────────────────────────────────

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender       = request.values.get("From", "")
    response     = MessagingResponse()
    msg          = response.message()

    # ── Voice note handling ───────────────────────────────────────
    try:
        num_media  = int(request.values.get("NumMedia", 0))
        media_url  = request.values.get("MediaUrl0", "")
        media_type = request.values.get("MediaContentType0", "")
        if num_media > 0 and media_url and "audio" in (media_type or ""):
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

    # ── Load / create patient ─────────────────────────────────────
    user = get_patient(sender) or {
        "phone": sender, "name": "", "week": 0,
        "step": "welcome", "language": "",
        "asha_id": "default_asha", "supervisor_id": "",
        "bmo_id": "", "village": "", "address": "", "status": "active"
    }
    if not get_patient(sender):
        save_patient(sender, "", 0, "welcome")

    # ── MONTH 4: detect "baby born" keyword → trigger delivery flow ─
    if user["step"] == "registered" and any(
        k in incoming_msg.lower() for k in [
            "baby born", "baby hua", "baccha hua", "delivered",
            "delivery ho gayi", "prasav", "baby aagaya"
        ]
    ):
        save_patient(
            sender, user["name"], user["week"],
            "get_delivery_date", user["language"],
            user.get("asha_id", "default_asha"),
            user.get("village", ""), user.get("address", ""),
            user.get("supervisor_id", ""), user.get("bmo_id", "")
        )
        msg.body(
            f"Mubarak ho {user['name']}! 🎉👶\n\n"
            "Delivery ki date kya thi?\n"
            "Please date bhejein — format: DD/MM/YYYY\n"
            "Example: 24/04/2026"
        )
        return str(response)

    # ── Delivery date collection (Month 4) ────────────────────────
    if user["step"] == "get_delivery_date":
        try:
            # Accept DD/MM/YYYY or YYYY-MM-DD
            raw = incoming_msg.strip()
            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                try:
                    ddate = datetime.strptime(raw, fmt)
                    delivery_str = ddate.strftime("%d %b %Y")
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("unrecognised date format")

            save_delivery_record(
                sender, delivery_str,
                asha_id=user.get("asha_id", "default_asha")
            )
            # Notify ASHA worker
            asha_info = get_asha_by_phone(user.get("asha_id", ""))
            if asha_info:
                send_whatsapp(
                    asha_info["phone"],
                    f"👶 *Delivery Registered*\n\n"
                    f"Patient: {user['name']}\n"
                    f"Phone: {sender}\n"
                    f"Delivery Date: {delivery_str}\n\n"
                    f"Please schedule Day 1 PNC visit. 🌸"
                )

            save_patient(
                sender, user["name"], user["week"],
                "registered", user["language"],
                user.get("asha_id", "default_asha"),
                user.get("village", ""), user.get("address", ""),
                user.get("supervisor_id", ""), user.get("bmo_id", "")
            )
            msg.body(
                f"Shukriya {user['name']}! Delivery {delivery_str} register "
                "ho gayi. 🌸\n\n"
                "Aapki ASHA worker aapko PNC check-in ke liye contact "
                "karegi.\n\n"
                "Postpartum danger signs batao agar feel ho:\n"
                "🔴 Bahut zyada bleeding\n🔴 Bukhaar\n"
                "🔴 Chest pain / breathing problem\n"
                "🔴 Wound se pus ya boo aa rahi ho"
            )
        except ValueError:
            msg.body(
                "Date samajh nahi aayi. Please DD/MM/YYYY format mein bhejein.\n"
                "Example: 24/04/2026"
            )
        return str(response)

    # ─────────────────────────────────────────────────────────────
    # REGISTRATION FLOW
    # ─────────────────────────────────────────────────────────────

    if incoming_msg.lower() in [
        "register", "register pregnancy",
        "hello", "hi", "start", "namaste"
    ]:
        if user["step"] == "registered":
            msg.body(
                f"🌸 Welcome back {user['name']}!\n\n"
                f"Aap week {user['week']} mein hain. Main hamesha yahan hoon. 💚\n\n"
                "Koi symptom feel ho toh batao, ya 'progress' type karo! 🌸"
            )
            return str(response)
        
        # 👉 NEW: Ask language
        save_patient(sender, "", 0, "select_language")
        msg.body(
            "🌸 Namaste! Welcome to MaaSakhi\n\n"
            "Please choose your language:\n\n"
            "1️. English\n"
            "2️⃣ Hindi\n"
            "3️⃣ Hinglish\n\n"
            "Reply with 1 / 2 / 3")
        return str(response)

        
        
    elif user["step"] == "select_language":
        choice = incoming_msg.strip()
        if choice == "1":
            lang = "English"
            reply = "Great! Let's continue in English. 😊"
        elif choice == "2":
            lang = "Hindi"
            reply = "Bahut badhiya! Hum Hindi mein baat karenge. 😊"
        elif choice == "3":
            lang = "Hinglish"
            reply = "Cool! Hinglish mein continue karte hain 😄"
        else:
            msg.body("Please reply with 1, 2 or 3.")
            return str(response)
        save_patient(sender, "", 0, "get_name", lang)
        msg.body(
            "🌸 Namaste! Welcome to MaaSakhi — aapki maternal health companion!\n\n"
            "Pehle mujhe apna naam batao:\nPlease tell me your name:"
        )
        return str(response)

    elif user["step"] == "ask_image_permission":
        choice = incoming_msg.strip()
        if choice == "1":
            save_patient(
                sender, user["name"], user["week"],
                "awaiting_image",
                user["language"],
                user.get("asha_id", "default_asha"),
                user.get("village", ""),
                user.get("address", ""),
                user.get("supervisor_id", ""),
                user.get("bmo_id", ""))
            msg.body(
                "📸 Theek hai!\n\n"
                "Kripya ab apni problem ka clear photo bhejein.\n"
                "Jaise: rash, swelling, wound etc.")
            return str(response)
        elif choice == "2":# Skip image → continue normal flow
            save_patient(
                sender, user["name"], user["week"],
                "registered",
                user["language"],
                user.get("asha_id", "default_asha"),
                user.get("village", ""),
                user.get("address", ""),
                user.get("supervisor_id", ""),
                user.get("bmo_id", "")
                )
            symptom = session.get("last_symptom", incoming_msg)
            level, reply, alert_needed = analyze(symptom, user["week"])
            save_symptom_log(sender, user["week"], symptom, level)
            msg.body(reply)
            return str(response)
        else:
            msg.body("Please 1 ya 2 mein se choose karein.")
            return str(response)
        
    elif user["step"] == "awaiting_image":
        num_media = int(request.values.get("NumMedia", 0))
        media_url = request.values.get("MediaUrl0", "")
        media_type = request.values.get("MediaContentType0", "")
        if num_media > 0 and "image" in (media_type or ""):
            # Send image to ASHA worker
            asha_info = get_asha_by_phone(user.get("asha_id", ""))
            if asha_info:
                send_whatsapp(
                    asha_info["phone"],
                    f"📸 *Patient Image Received*\n\n"
                    f"Name: {user['name']}\n"
                    f"Phone: {sender}\n\n"
                    f"🔗 Image: {media_url}"
                )
            # Continue analysis
            symptom = session.get("last_symptom", "")
            level, reply, alert_needed = analyze(symptom, user["week"])
            save_symptom_log(sender, user["week"], symptom, level)
            # Reset step
            save_patient(
                sender, user["name"], user["week"],
                "registered",
                user["language"],
                user.get("asha_id", "default_asha"),
                user.get("village", ""),
                user.get("address", ""),
                user.get("supervisor_id", ""),
                user.get("bmo_id", ""))
            msg.body(
                f"✅ Photo mil gaya.\n\n{reply}\n\n"
                "ASHA worker ko bhi bhej diya gaya hai. 💚")
            return str(response)
        else:
            msg.body("Kripya ek clear image bhejein 📸")
            return str(response)
    


    elif user["step"] == "get_name":
        save_patient(sender, incoming_msg, 0, "get_week")
        msg.body(
            f"Namaste {incoming_msg}! 🙏\n\n"
            "Aap kitne hafte ki pregnant hain?\n"
            "How many weeks pregnant are you?\n\nSirf number — Example: 26"
        )

    elif user["step"] == "get_week":
        try:
            week = int(incoming_msg)
            save_patient(sender, user["name"], week, "get_village")
            msg.body(
                "Shukriya! 🌸\n\nAap kis gaon mein rehti hain?\n"
                "Which village do you live in?\n\nExample: Rampur"
            )
        except ValueError:
            msg.body("Sirf number bhejiye. Example: 26")

    elif user["step"] == "get_village":
        village = incoming_msg.strip()
        asha    = get_asha_by_village(village)
        asha_id       = asha["asha_id"]             if asha else "default_asha"
        supervisor_id = asha.get("supervisor_id","") if asha else ""
        bmo_id        = _bmo_id_from_supervisor(supervisor_id)

        save_patient(
            sender, user["name"], user["week"], "get_address",
            user["language"], asha_id, village, "",
            supervisor_id, bmo_id
        )
        msg.body(
            f"Shukriya {user['name']}! 🌸\n\n"
            "Ab apna ghar ka address batao —\n"
            "gali, mohalla ya koi pehchaan ki jagah.\n\n"
            "Example: Near Govt School, Ward 4, Rampur\n\n"
            "(Yeh ASHA worker ko emergency mein dhundhne mein madad karega 🏥)"
        )

    elif user["step"] == "get_address":
        address = incoming_msg.strip()
        user    = get_patient(sender)   # reload with saved asha_id etc.
        save_patient(
            sender, user["name"], user["week"], "registered",
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
            f"📍 Village: {user.get('village','')}\n"
            f"🏠 Address: {address}\n\n"
            f"Main aapke saath hoon 24/7. 💚\n\n"
            f"{tip_msg}\n\n"
            "Koi bhi symptom feel ho — bas mujhe message karo. 🌸\n\n"
            "💡 Tip: 'baby born' type karo jab delivery ho jaaye."
        )

    # ─────────────────────────────────────────────────────────────
    # REGISTERED — symptom analysis + scheme queries
    # ─────────────────────────────────────────────────────────────

    elif user["step"] == "registered":

        # ── Recovery confirmation ─────────────────────────────────
        recovery = handle_recovery_confirmation(incoming_msg)
        if recovery == "BETTER":
            alert = get_alert_by_patient_phone(sender)
            if alert and alert["status"] == "Attended":
                update_alert_status(alert["id"], "Resolved")
                msg.body(
                    f"🌸 Bahut khushi hui, {user['name']}!\n\n"
                    "✅ Aapki recovery confirm ho gayi.\n"
                    "ASHA worker ko inform kar diya gaya hai. 💚"
                )
            else:
                msg.body(f"Khushi hui sunke {user['name']}! 🌸 Apna khayal rakhein. 💚")
            return str(response)

        if recovery == "NOT_WELL":
            save_asha_alert_db(
                sender, user["name"], user["week"],
                "FOLLOW UP: Patient still not feeling well",
                user.get("asha_id", "default_asha"),
                address=user.get("address", ""),
                village=user.get("village", ""),
                supervisor_id=user.get("supervisor_id", ""),
                bmo_id=user.get("bmo_id", "")
            )
            msg.body(
                f"🚨 ASHA worker ko dobara alert kar diya gaya hai, {user['name']}.\n\n"
                "Please nearest health centre zaroor jaayein. 🏥\n\nAap akeli nahi hain. 💚"
            )
            return str(response)

        # ── Month 1: govt scheme queries ──────────────────────────
        if any(k in incoming_msg.lower() for k in [
            "yojana", "scheme", "sarkar", "benefit", "pmmvy",
            "jsy", "jssk", "ayushman", "rajshri", "paisa"
        ]):
            from dashboard import GOVT_SCHEMES
            scheme_reply = "🏛️ *Aapke liye sarkari yojanaayein:*\n\n"
            for s in GOVT_SCHEMES[:3]:
                scheme_reply += (
                    f"*{s['name']}*\n"
                    f"💰 {s['amount']}\n"
                    f"✅ {s['eligibility']}\n"
                    f"📝 {s['how_to_apply']}\n\n"
                )
            scheme_reply += "Aapki ASHA worker in yojanaon mein madad karegi. 🌸"
            msg.body(scheme_reply)
            return str(response)

        # ── Update language ───────────────────────────────────────
        # ✅ Smart language handling
        detected_lang = detect_language(incoming_msg)
        # Case 1: If user has NOT selected language yet → use detection
        if not user.get("language"):
            save_patient(
                sender, user["name"], user["week"], "registered",
                detected_lang,
                user.get("asha_id", "default_asha"),
                user.get("village", ""),
                user.get("address", ""),
                user.get("supervisor_id", ""),
                user.get("bmo_id", "")
            )
            user["language"] = detected_lang
        # Case 2: If user selected language → DO NOT override
        # (Optional advanced: allow switching if user clearly changes language)
        elif detected_lang != user["language"]:
            # Only update if user is consistently using another language
            # # (you can remove this block if you want strict locking)
            pass

        # ── Progress tracker ──────────────────────────────────────
        if is_tracker_request(incoming_msg):
            reply = get_progress_update(
                user["week"], user["name"], sender, user["language"]
            )
            msg.body(reply)
            return str(response)
        


        #Visual Input --------------------
        # ✅ Check if symptom is visual
        if is_visual_symptom(incoming_msg):
            save_patient(
                sender, user["name"], user["week"],
                "ask_image_permission",
                user["language"],
                user.get("asha_id", "default_asha"),
                user.get("village", ""),
                user.get("address", ""),
                user.get("supervisor_id", ""),
                user.get("bmo_id", "")
                )
            # store last symptom temporarily 
            session["last_symptom"] = incoming_msg
            msg.body(
                "📸 Kya aap apni problem ka photo share karna chahengi?\n\n"
                "1️⃣ Haan (Yes)\n"
                "2️⃣ Nahi (No)" 
                )
            return str(response)



        # ── AI symptom analysis ───────────────────────────────────
        # Route postpartum symptoms differently (Month 4)
        is_postpartum = user.get("status") == "postpartum"
        level, reply, alert_needed = analyze(
            incoming_msg, user["week"],
            postpartum=is_postpartum
        )
        save_symptom_log(sender, user["week"], incoming_msg, level)

        if level == "RED":
            maps_link = _maps_link(
                user.get("address", ""), user.get("village", "")
            )
            save_asha_alert_db(
                sender, user["name"], user["week"], incoming_msg,
                user.get("asha_id", "default_asha"),
                address=user.get("address", ""),
                village=user.get("village", ""),
                maps_link=maps_link,
                supervisor_id=user.get("supervisor_id", ""),
                bmo_id=user.get("bmo_id", "")
            )
            save_alert(
                user["name"], user["week"], incoming_msg, sender,
                user.get("asha_id", "default_asha"),
                address=user.get("address", ""),
                village=user.get("village", "")
            )
            msg.body(
                f"{reply}\n\n"
                "Aapki ASHA worker ko alert kar diya gaya hai.\n"
                "Please go to your nearest health centre immediately. 🏥"
            )
        elif level == "AMBER":
            msg.body(f"{reply}\n\nAgar 24 ghante mein better na ho — mujhe zaroor batana. 💛")
        else:
            msg.body(f"{reply}\n\nKoi aur symptom ho toh batao! 💚")

    else:
        msg.body("Namaste! 'Register' ya 'Hello' type karke shuru karein. 🌸")

    return str(response)



# ─────────────────────────────────────────────────────────────────
# UNIFIED LOGIN
# ─────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        clean = phone.replace("+91","").replace(" ","").replace("-","")
        if len(clean) == 10 and clean.isdigit():
            wa_phone    = "whatsapp:+91" + clean
            plain_phone = "+91" + clean
        else:
            wa_phone = plain_phone = phone

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

    return f"""
    <!DOCTYPE html><html><head><title>MaaSakhi Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'Poppins',sans-serif;
              background:linear-gradient(135deg,#085041,#0a6b52);
              min-height:100vh;display:flex;justify-content:center;align-items:center}}
        .box{{background:white;padding:36px 32px;border-radius:16px;
              box-shadow:0 20px 60px rgba(0,0,0,0.2);
              width:90%;max-width:380px;text-align:center}}
        .logo{{font-size:36px;margin-bottom:6px}}
        h2{{font-size:20px;color:#085041}}
        p{{font-size:13px;color:#666;margin-top:4px}}
        .roles{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:20px 0 16px}}
        .role-badge{{padding:8px;border-radius:8px;font-size:11px;font-weight:600}}
        input{{width:100%;padding:13px;margin-top:4px;border-radius:8px;
               border:1.5px solid #e5e7eb;font-family:'Poppins',sans-serif;font-size:14px}}
        input:focus{{outline:none;border-color:#085041}}
        button{{margin-top:16px;width:100%;padding:13px;background:#085041;
                color:white;border:none;border-radius:8px;font-size:15px;
                font-weight:600;cursor:pointer;font-family:'Poppins',sans-serif}}
        button:hover{{background:#0a6b52}}
        .error{{background:#fef2f2;color:#dc2626;padding:10px;
                border-radius:8px;font-size:13px;margin-top:12px}}
        a.back{{display:block;margin-top:16px;font-size:12px;color:#085041;text-decoration:none}}
        a.admin{{display:block;margin-top:10px;font-size:12px;color:#7C3AED;text-decoration:none}}
    </style></head><body>
    <div class="box">
        <div class="logo">🌿</div>
        <h2>MaaSakhi Login</h2>
        <p>One login for all health workers</p>
        <div class="roles">
            <div class="role-badge" style="background:#e6f4f1;color:#085041">👩 ASHA Worker</div>
            <div class="role-badge" style="background:#e0f0ff;color:#0369A1">👩‍💼 Supervisor</div>
            <div class="role-badge" style="background:#fff3e0;color:#B45309">🏥 BMO</div>
            <div class="role-badge" style="background:#f3e8ff;color:#7C3AED">🏛 DHO → Admin</div>
        </div>
        <form method="POST">
            <input name="phone" placeholder="Enter your 10-digit mobile number"
                   pattern="[0-9+\\s-]{{10,14}}" required>
            {"<div class='error'>" + error + "</div>" if error else ""}
            <button type="submit">Login →</button>
        </form>
        <a href="/" class="back">← Back to Home</a>
        <a href="/admin/login" class="admin">🔐 District Admin Login</a>
    </div></body></html>
    """


# ─────────────────────────────────────────────────────────────────
# ASHA WORKER DASHBOARD + ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/dashboard/<asha_id>")
def dashboard(asha_id):
    patients  = get_all_patients(asha_id)
    alerts    = get_all_asha_alerts(asha_id)
    high_risk = len([a for a in alerts if a["status"] != "Resolved"])
    safe      = max(len(patients) - high_risk, 0)
    return render_dashboard(patients, high_risk, len(patients), safe, asha_id)


@app.route("/dashboard/<asha_id>/attend/<int:alert_id>", methods=["POST"])
def mark_attended(asha_id, alert_id):
    update_alert_status(alert_id, "Attended")
    try:
        from sqlalchemy import text as sqlt
        with engine.connect() as conn:
            result = conn.execute(
                sqlt("SELECT * FROM asha_alerts WHERE id = :id"),
                {"id": alert_id}
            ).fetchone()
            if result:
                asha_row = conn.execute(
                    sqlt("SELECT name FROM asha_workers WHERE asha_id = :id"),
                    {"id": asha_id}
                ).fetchone()
                asha_name = asha_row.name if asha_row else "Aapki ASHA worker"
                send_whatsapp(
                    result.phone,
                    f"🌸 Namaste {result.name}!\n\n"
                    f"*{asha_name}* ne aapka case attend kar liya hai. 💚\n\n"
                    "Kya aap ab theek feel kar rahi hain?\n\n"
                    "✅ *'I am better'* — agar theek hain\n"
                    "⚠️ *'Still not feeling well'* — agar takleef hai"
                )
    except Exception as e:
        print(f"Attend alert error: {e}")
    return redirect(f"/dashboard/{asha_id}")


@app.route("/dashboard/<asha_id>/log-visit/<int:alert_id>", methods=["POST"])
def log_visit(asha_id, alert_id):
    """Month 1 — ASHA logs visit outcome."""
    outcome     = request.form.get("outcome",     "stable")
    notes       = request.form.get("notes",       "")
    referred_to = request.form.get("referred_to", "")

    alert = get_alert_by_id(alert_id)
    if alert:
        save_asha_visit(
            alert_id=alert_id, phone=alert["phone"],
            patient_name=alert["name"], asha_id=asha_id,
            outcome=outcome, notes=notes, referred_to=referred_to
        )
        if outcome in ["referred_phc", "referred_hospital", "called_108"]:
            update_alert_status(
                alert_id, "Resolved",
                notes=f"Referred to: {referred_to}" if referred_to else outcome
            )
            # WhatsApp to patient
            send_whatsapp(
                alert["phone"],
                f"🌸 {alert['name']}, aapki ASHA worker ne aapko "
                f"*{referred_to or outcome.replace('_',' ')}* ke liye "
                "refer kar diya hai.\n\nPlease jald se jald wahan jaayein. 🏥"
            )
        elif outcome == "not_found":
            update_alert_status(alert_id, "Pending", notes="Not found at address")
        else:
            update_alert_status(alert_id, "Attended", notes=notes)
    return redirect(f"/dashboard/{asha_id}")


@app.route("/dashboard/<asha_id>/log-anc", methods=["POST"])
def log_anc(asha_id):
    """Month 1 / Month 3 — Log ANC visit for a patient."""
    patient_phone = request.form.get("patient_phone", "")
    visit_number  = int(request.form.get("visit_number", 1))
    visit_date    = request.form.get("visit_date", "")
    notes         = request.form.get("notes", "")

    if patient_phone:
        save_anc_record(patient_phone, visit_number, visit_date, asha_id, notes)
        # Remind patient
        patient = get_patient(patient_phone)
        if patient:
            next_visit = {1:"14–16 weeks",2:"28–32 weeks",3:"36 weeks",4:"Delivery"}.get(visit_number + 1)
            if next_visit:
                send_whatsapp(
                    patient_phone,
                    f"✅ {patient['name']}, aapki ANC {visit_number} visit "
                    f"record ho gayi. 🌸\n\nAgli ANC visit: {next_visit} mein. "
                    "Apna khayal rakhein! 💚"
                )
    return redirect(f"/dashboard/{asha_id}?tab=patients")


@app.route("/dashboard/<asha_id>/log-scheme", methods=["POST"])
def log_scheme(asha_id):
    """Month 1 — Log govt scheme delivery to patient."""
    patient_phone = request.form.get("patient_phone", "")
    scheme_name   = request.form.get("scheme_name", "")
    amount        = request.form.get("amount", "")

    if patient_phone and scheme_name:
        patient = get_patient(patient_phone)
        if patient:
            save_scheme_delivery(
                patient_phone, patient["name"],
                scheme_name, amount, asha_id
            )
    return redirect(f"/dashboard/{asha_id}?tab=schemes")


@app.route("/dashboard/<asha_id>/register-delivery", methods=["POST"])
def register_delivery(asha_id):
    """Month 4 — Register a delivery from ASHA dashboard."""
    patient_phone = request.form.get("patient_phone", "")
    raw_date      = request.form.get("delivery_date", "")
    birth_weight  = request.form.get("birth_weight",  "")
    delivery_mode = request.form.get("delivery_mode", "normal")
    facility      = request.form.get("facility",      "")

    if patient_phone and raw_date:
        try:
            ddate        = datetime.strptime(raw_date, "%Y-%m-%d")
            delivery_str = ddate.strftime("%d %b %Y")
        except ValueError:
            delivery_str = raw_date

        save_delivery_record(
            patient_phone, delivery_str, birth_weight,
            delivery_mode, facility, asha_id
        )
        patient = get_patient(patient_phone)
        if patient:
            send_whatsapp(
                patient_phone,
                f"🎉 Mubarak ho {patient['name']}!\n\n"
                f"Aapki delivery {delivery_str} register ho gayi hai.\n"
                "Aapki ASHA worker PNC check-in ke liye sampark karegi. 🌸"
            )
    return redirect(f"/dashboard/{asha_id}?tab=postpartum")


@app.route("/dashboard/<asha_id>/log-pnc/<phone>", methods=["POST"])
def log_pnc(asha_id, phone):
    """Month 4 — Mark PNC visit done."""
    patient = get_patient(phone)
    if patient:
        delivery = get_delivery_record(phone)
        if delivery:
            try:
                from datetime import date
                ddate     = datetime.strptime(delivery["delivery_date"], "%d %b %Y").date()
                days_done = (date.today() - ddate).days
                save_anc_record(
                    phone, days_done, date.today().strftime("%d %b %Y"),
                    asha_id, notes=f"PNC Day {days_done}"
                )
            except Exception as e:
                print(f"PNC log error: {e}")
        send_whatsapp(
            phone,
            f"✅ {patient['name']}, aapki aaj ki PNC visit record ho gayi. 🌸\n"
            "Koi bhi problem ho toh mujhe batao. 💚"
        )
    return redirect(f"/dashboard/{asha_id}?tab=postpartum")


@app.route("/dashboard/<asha_id>/log-growth/<int:child_id>", methods=["POST"])
def log_growth(asha_id, child_id):
    """Month 4 — Log child growth measurement."""
    mother_phone = request.form.get("mother_phone", "")
    try:
        weight_kg  = float(request.form.get("weight_kg",  0))
        height_cm  = float(request.form.get("height_cm",  0))
        age_months = int(request.form.get("age_months", 0))
    except ValueError:
        return redirect(f"/dashboard/{asha_id}?tab=postpartum")

    # Simple WHO z-score approximation (weight-for-age)
    # Reference median for boys, rough approximation
    who_medians = {0:3.3,1:4.5,2:5.6,3:6.4,4:7.0,5:7.5,6:7.9,
                   9:9.2,12:9.6,18:10.9,24:12.2,36:14.3}
    closest_age = min(who_medians.keys(), key=lambda x: abs(x - age_months))
    median      = who_medians[closest_age]
    z_score     = round((weight_kg - median) / (median * 0.15), 2)
    status      = ("Normal" if z_score >= -1
                   else "Moderate Undernutrition" if z_score >= -2
                   else "Severe Undernutrition")

    save_growth_log(child_id, mother_phone, weight_kg, height_cm,
                    age_months, z_score, status)

    # Alert ASHA if severe undernutrition
    if z_score < -2:
        asha_info = get_asha_by_phone(asha_id)
        if asha_info:
            send_whatsapp(
                asha_info["phone"],
                f"⚠️ *Growth Alert*\n\n"
                f"Child ID {child_id} (Mother: {mother_phone})\n"
                f"Weight: {weight_kg} kg at {age_months} months\n"
                f"Z-score: {z_score} — *{status}*\n\n"
                "Please refer to NRC if needed."
            )
    return redirect(f"/dashboard/{asha_id}?tab=postpartum")


@app.route("/dashboard/<asha_id>/log-vaccine/<int:child_id>", methods=["POST"])
def log_vaccine(asha_id, child_id):
    """Month 4 — Record a vaccination."""
    mother_phone = request.form.get("mother_phone", "")
    vaccine_name = request.form.get("vaccine_name", "")
    given_date   = request.form.get("given_date",   "")
    given_by     = request.form.get("given_by",     "")

    if vaccine_name and given_date:
        save_immunization_record(
            child_id, mother_phone, vaccine_name,
            1, given_date, given_by=given_by
        )
        patient = get_patient(mother_phone)
        if patient:
            send_whatsapp(
                mother_phone,
                f"💉 {patient['name']}, aapke bacche ko aaj "
                f"*{vaccine_name}* vaccine lagi. ✅\n\n"
                "Agle teeke ke liye ASHA worker aapko batayegi. 🌸"
            )
    return redirect(f"/dashboard/{asha_id}?tab=postpartum")


# ─────────────────────────────────────────────────────────────────
# SUPERVISOR DASHBOARD + ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/supervisor/<supervisor_id>")
def supervisor_dashboard(supervisor_id):
    stats   = get_supervisor_stats(supervisor_id)
    ashas   = get_supervisor_ashas(supervisor_id)
    alerts  = get_supervisor_alerts(supervisor_id)
    tab     = request.args.get("tab", "alerts")

    # Build ASHA performance rows
    perf_rows = ""
    for a in ashas:
        rating = a.get("avg_response_hrs")
        if rating is None:
            rating_html = '<span style="color:#9ca3af">No data</span>'
        elif rating <= 1:
            rating_html = '<span style="color:#16a34a;font-weight:600">🟢 Excellent</span>'
        elif rating <= 3:
            rating_html = '<span style="color:#b45309;font-weight:600">🟡 Good</span>'
        else:
            rating_html = '<span style="color:#dc2626;font-weight:600">🔴 Slow</span>'

        perf_rows += f"""
        <tr>
            <td style="padding:10px;font-weight:500">{a['name']}</td>
            <td style="padding:10px">{a['village']}</td>
            <td style="padding:10px;text-align:center">{a['patient_count']}</td>
            <td style="padding:10px;text-align:center;color:#ef4444;font-weight:600">{a['pending_alerts']}</td>
            <td style="padding:10px;text-align:center;color:#10b981;font-weight:600">{a['resolved_alerts']}</td>
            <td style="padding:10px;text-align:center">{rating_html}</td>
            <td style="padding:10px">
                <a href="/dashboard/{a['asha_id']}" target="_blank"
                   style="color:#0369A1;font-size:12px">View →</a>
            </td>
        </tr>
        """

    alerts_html = ""
    for a in alerts:
        maps_btn = (f'<a href="{a["maps_link"]}" target="_blank" '
                    f'style="color:#0369A1;font-size:12px">📌 Navigate</a>'
                    if a.get("maps_link") else "")
        esc_btn = ""
        if a["status"] == "Pending" and a.get("level", 0) < 2:
            esc_btn = (
                f'<form method="POST" action="/supervisor/{supervisor_id}'
                f'/escalate/{a["id"]}" style="display:inline">'
                '<button style="background:#dc2626;color:white;border:none;'
                'padding:5px 12px;border-radius:6px;font-size:11px;cursor:pointer">'
                '⬆ Escalate to BMO</button></form>'
            )
        status_colour = {"Pending":"#dc2626","Attended":"#b45309","Resolved":"#16a34a"}.get(a["status"],"#888")
        alerts_html += f"""
        <div style="background:white;border-radius:12px;padding:14px;
                    margin-bottom:10px;border-left:4px solid {status_colour}">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <strong>{a['name']}</strong>
                <span style="font-size:11px;font-weight:700;color:{status_colour}">{a['status']}</span>
            </div>
            <div style="font-size:12.5px;color:#555;margin-top:4px">
                Week {a['week']} · {a['symptom'][:60]}
            </div>
            <div style="font-size:11.5px;color:#888;margin-top:3px">
                ASHA: {a.get('asha_name','—')} · {a.get('village','—')} · {a['time']}
            </div>
            <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">
                {maps_btn}{esc_btn}
            </div>
        </div>
        """

    tab_style = lambda t: (
        "color:white;border-bottom:2px solid #4ade80;background:transparent"
        if t == tab else
        "color:rgba(255,255,255,0.6);border-bottom:2px solid transparent;background:transparent"
    )

    return f"""
    <!DOCTYPE html><html><head>
    <title>Supervisor Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'DM Sans',sans-serif;background:#f0f4ff;color:#111827}}
        .header{{background:#0369A1;color:white;padding:20px 24px}}
        .header h1{{font-size:20px;font-weight:700}}
        .header p{{font-size:12px;opacity:0.8;margin-top:4px}}
        .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;padding:18px 20px}}
        .stat{{background:white;border-radius:12px;padding:14px;text-align:center;border:1px solid #e0eaff}}
        .stat-n{{font-size:28px;font-weight:700}}
        .stat-l{{font-size:10px;color:#888;margin-top:3px;text-transform:uppercase;letter-spacing:.04em}}
        .tab-nav{{display:flex;background:#0369A1;padding:0 20px;gap:2px;overflow-x:auto}}
        .tab-btn{{padding:10px 16px;border:none;font-family:'DM Sans',sans-serif;
                  font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}}
        .panel{{padding:0 20px 20px}}
        table{{width:100%;border-collapse:collapse;background:white;
               border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.05)}}
        th{{background:#f8fafc;padding:10px;font-size:11px;text-align:left;
            color:#6b7280;text-transform:uppercase;letter-spacing:.04em}}
        tr:hover{{background:#f9fafb}}
        .footer{{text-align:center;font-size:11px;color:#9ca3af;padding:20px}}
        .footer a{{color:#0369A1;text-decoration:none}}
    </style></head><body>
    <div class="header">
        <h1>👩‍💼 Supervisor Dashboard</h1>
        <p>Live · Auto-refreshes every 30 s · Block Level</p>
    </div>
    <div class="stats">
        <div class="stat">
            <div class="stat-n" style="color:#0369A1">{stats.get('total_ashas',0)}</div>
            <div class="stat-l">ASHA Workers</div>
        </div>
        <div class="stat">
            <div class="stat-n" style="color:#085041">{stats.get('total_patients',0)}</div>
            <div class="stat-l">Patients</div>
        </div>
        <div class="stat">
            <div class="stat-n" style="color:#ef4444">{stats.get('pending_alerts',0)}</div>
            <div class="stat-l">Pending</div>
        </div>
        <div class="stat">
            <div class="stat-n" style="color:#f59e0b">{stats.get('escalated_to_me',0)}</div>
            <div class="stat-l">Escalated</div>
        </div>
        <div class="stat">
            <div class="stat-n" style="color:#10b981">{stats.get('resolved_this_week',0)}</div>
            <div class="stat-l">Resolved (7d)</div>
        </div>
    </div>
    <div class="tab-nav">
        <button class="tab-btn" style="{tab_style('alerts')}"
                onclick="location='?tab=alerts'">⚠️ Alerts</button>
        <button class="tab-btn" style="{tab_style('ashas')}"
                onclick="location='?tab=ashas'">👩 ASHA Workers</button>
        <button class="tab-btn" style="{tab_style('performance')}"
                onclick="location='?tab=performance'">📊 Performance</button>
    </div>
    <div class="panel" style="padding-top:16px">
        {"<div>" + alerts_html + "</div>" if tab == "alerts" else ""}
        {f'''
        <div style="overflow-x:auto">
        <table>
            <thead><tr>
                <th>Name</th><th>Village</th><th>Patients</th>
                <th>Pending</th><th>Resolved</th><th>Avg Response</th><th></th>
            </tr></thead>
            <tbody>{perf_rows}</tbody>
        </table></div>
        ''' if tab in ("ashas","performance") else ""
        }
    </div>
    <div class="footer">MaaSakhi · <a href="/login">← Logout</a></div>
    </body></html>
    """


@app.route("/supervisor/<supervisor_id>/escalate/<int:alert_id>", methods=["POST"])
def supervisor_escalate(supervisor_id, alert_id):
    from escalation import trigger_manual_escalation
    trigger_manual_escalation(alert_id)
    return redirect(f"/supervisor/{supervisor_id}")


# ─────────────────────────────────────────────────────────────────
# BMO DASHBOARD + ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/bmo/<bmo_id>")
def bmo_dashboard(bmo_id):
    stats  = get_bmo_stats(bmo_id)
    alerts = get_bmo_alerts(bmo_id)
    tab    = request.args.get("tab", "alerts")

    alerts_html = ""
    for a in alerts:
        maps_btn = (f'<a href="{a["maps_link"]}" target="_blank" '
                    f'style="color:#B45309;font-size:12px">📌 Navigate</a>'
                    if a.get("maps_link") else "")
        alerts_html += f"""
        <div style="background:white;border-radius:12px;padding:16px;
                    margin-bottom:12px;border-left:4px solid #dc2626">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <strong>🚨 {a['name']}</strong>
                <span style="font-size:11px;font-weight:700;color:#dc2626">ESCALATED</span>
            </div>
            <div style="font-size:13px;color:#555;margin-top:4px">
                Week {a['week']} · {a['symptom'][:70]}
            </div>
            <div style="font-size:11.5px;color:#888;margin-top:3px">
                ASHA: {a.get('asha_name','—')} · Village: {a.get('village','—')}
            </div>
            <div style="font-size:11.5px;color:#888">
                Address: {a.get('address','—')} · 📞 {a['phone']} · {a['time']}
            </div>
            <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">
                {maps_btn}
                <form method="POST" action="/bmo/{bmo_id}/resolve/{a['id']}" style="display:inline">
                    <button style="background:#085041;color:white;border:none;
                                   padding:7px 14px;border-radius:7px;
                                   font-size:12px;cursor:pointer">✅ Resolve</button>
                </form>
                <form method="POST" action="/bmo/{bmo_id}/escalate/{a['id']}" style="display:inline">
                    <button style="background:#7C3AED;color:white;border:none;
                                   padding:7px 14px;border-radius:7px;
                                   font-size:12px;cursor:pointer">⬆ Escalate to DHO</button>
                </form>
                <a href="tel:{a['phone']}"
                   style="display:inline-block;background:#8b5cf6;color:white;
                          padding:7px 14px;border-radius:7px;font-size:12px;
                          text-decoration:none">📞 Call Patient</a>
            </div>
        </div>
        """

    tab_style = lambda t: (
        "color:white;border-bottom:2px solid #fbbf24" if t == tab
        else "color:rgba(255,255,255,0.6);border-bottom:2px solid transparent"
    )

    return f"""
    <!DOCTYPE html><html><head>
    <title>BMO Dashboard — MaaSakhi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'DM Sans',sans-serif;background:#fff8f0;color:#111827}}
        .header{{background:#B45309;color:white;padding:20px 24px}}
        .header h1{{font-size:20px;font-weight:700}}
        .header p{{font-size:12px;opacity:0.8;margin-top:4px}}
        .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;padding:18px 20px}}
        .stat{{background:white;border-radius:12px;padding:14px;text-align:center;border:1px solid #fde8c8}}
        .stat-n{{font-size:28px;font-weight:700}}
        .stat-l{{font-size:10px;color:#888;margin-top:3px;text-transform:uppercase;letter-spacing:.04em}}
        .tab-nav{{display:flex;background:#B45309;padding:0 20px;gap:2px;overflow-x:auto}}
        .tab-btn{{padding:10px 16px;border:none;background:transparent;
                  font-family:'DM Sans',sans-serif;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}}
        .panel{{padding:16px 20px 20px}}
        .footer{{text-align:center;font-size:11px;color:#9ca3af;padding:20px}}
        .footer a{{color:#B45309;text-decoration:none}}
    </style></head><body>
    <div class="header">
        <h1>🏥 Block Medical Officer Dashboard</h1>
        <p>Live · Critical escalations requiring block-level intervention</p>
    </div>
    <div class="stats">
        <div class="stat">
            <div class="stat-n" style="color:#0369A1">{stats.get('total_supervisors',0)}</div>
            <div class="stat-l">Supervisors</div>
        </div>
        <div class="stat">
            <div class="stat-n" style="color:#085041">{stats.get('total_ashas',0)}</div>
            <div class="stat-l">ASHA Workers</div>
        </div>
        <div class="stat">
            <div class="stat-n" style="color:#085041">{stats.get('total_patients',0)}</div>
            <div class="stat-l">Patients</div>
        </div>
        <div class="stat">
            <div class="stat-n" style="color:#ef4444">{stats.get('pending_in_block',0)}</div>
            <div class="stat-l">Pending</div>
        </div>
        <div class="stat">
            <div class="stat-n" style="color:#dc2626">{stats.get('escalated_alerts',0)}</div>
            <div class="stat-l">Escalated</div>
        </div>
    </div>
    <div class="tab-nav">
        <button class="tab-btn" style="{tab_style('alerts')}"
                onclick="location='?tab=alerts'">🚨 Escalated Alerts</button>
        <button class="tab-btn" style="{tab_style('patients')}"
                onclick="location='?tab=patients'">👥 Block Patients</button>
    </div>
    <div class="panel">
        {"<div>" + (alerts_html or '<p style="color:#9ca3af;text-align:center;padding:30px">✅ No escalated alerts</p>') + "</div>"
         if tab == "alerts" else ""}
        {"<p style='color:#9ca3af;text-align:center;padding:30px'>Patient list — use admin panel for full view.</p>"
         if tab == "patients" else ""}
    </div>
    <div class="footer">MaaSakhi BMO Dashboard · <a href="/login">← Logout</a></div>
    <script>setTimeout(()=>location.reload(),30000);</script>
    </body></html>
    """


@app.route("/bmo/<bmo_id>/escalate/<int:alert_id>", methods=["POST"])
def bmo_escalate(bmo_id, alert_id):
    from escalation import trigger_manual_escalation
    trigger_manual_escalation(alert_id)
    return redirect(f"/bmo/{bmo_id}")


@app.route("/bmo/<bmo_id>/resolve/<int:alert_id>", methods=["POST"])
def bmo_resolve(bmo_id, alert_id):
    update_alert_status(alert_id, "Resolved", notes="Resolved by BMO")
    alert = get_alert_by_id(alert_id)
    if alert:
        send_whatsapp(
            alert["phone"],
            f"✅ {alert['name']}, aapka case Block Medical Officer ne "
            "resolve kar diya hai. 💚\nApna khayal rakhein! 🌸"
        )
    return redirect(f"/bmo/{bmo_id}")


# ─────────────────────────────────────────────────────────────────
# ADMIN / DHO ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin = verify_admin(
            request.form.get("username"),
            request.form.get("password")
        )
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
    return render_admin_panel(
        admin_name=session["admin"]["name"],
        tab=request.args.get("tab", "asha")
    )


# ── ASHA management ───────────────────────────────────────────────
@app.route("/admin/add-asha", methods=["POST"])
def admin_add_asha():
    if "admin" not in session:
        return redirect("/admin/login")
    ok = add_asha_worker(
        asha_id       = request.form.get("asha_id",       "").strip(),
        name          = request.form.get("name",          "").strip(),
        phone         = request.form.get("phone",         "").strip(),
        village       = request.form.get("village",       "").strip(),
        district      = request.form.get("district",      "").strip(),
        block_name    = request.form.get("block_name",    "").strip(),
        supervisor_id = request.form.get("supervisor_id", "").strip()
    )
    return render_admin_panel(
        admin_name=session["admin"]["name"], tab="asha",
        message="ASHA worker added!" if ok else "Failed to add ASHA worker.",
        success=ok
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


# ── Supervisor management ─────────────────────────────────────────
@app.route("/admin/add-supervisor", methods=["POST"])
def admin_add_supervisor():
    if "admin" not in session:
        return redirect("/admin/login")
    ok = add_asha_supervisor(
        supervisor_id = request.form.get("supervisor_id", "").strip(),
        name          = request.form.get("name",          "").strip(),
        phone         = request.form.get("phone",         "").strip(),
        block_name    = request.form.get("block_name",    "").strip(),
        district      = request.form.get("district",      "").strip(),
        bmo_id        = request.form.get("bmo_id",        "").strip()
    )
    return render_admin_panel(
        admin_name=session["admin"]["name"], tab="supervisors",
        message="Supervisor added!" if ok else "Failed.",
        success=ok
    )


@app.route("/admin/toggle-supervisor", methods=["POST"])
def admin_toggle_supervisor():
    if "admin" not in session:
        return redirect("/admin/login")
    toggle_supervisor_status(request.form.get("supervisor_id"))
    return redirect("/admin?tab=supervisors")


@app.route("/admin/delete-supervisor", methods=["POST"])
def admin_delete_supervisor():
    if "admin" not in session:
        return redirect("/admin/login")
    delete_supervisor(request.form.get("supervisor_id"))
    return redirect("/admin?tab=supervisors")


# ── BMO management ────────────────────────────────────────────────
@app.route("/admin/add-bmo", methods=["POST"])
def admin_add_bmo():
    if "admin" not in session:
        return redirect("/admin/login")
    ok = add_block_officer(
        bmo_id     = request.form.get("bmo_id",     "").strip(),
        name       = request.form.get("name",       "").strip(),
        phone      = request.form.get("phone",      "").strip(),
        block_name = request.form.get("block_name", "").strip(),
        district   = request.form.get("district",   "").strip()
    )
    return render_admin_panel(
        admin_name=session["admin"]["name"], tab="bmo",
        message="BMO added!" if ok else "Failed.",
        success=ok
    )


@app.route("/admin/toggle-bmo", methods=["POST"])
def admin_toggle_bmo():
    if "admin" not in session:
        return redirect("/admin/login")
    toggle_bmo_status(request.form.get("bmo_id"))
    return redirect("/admin?tab=bmo")


@app.route("/admin/delete-bmo", methods=["POST"])
def admin_delete_bmo():
    if "admin" not in session:
        return redirect("/admin/login")
    delete_block_officer(request.form.get("bmo_id"))
    return redirect("/admin?tab=bmo")


# ── Month 3: Analytics API ────────────────────────────────────────
@app.route("/admin/api/trends")
def api_trends():
    """JSON endpoint for district trend charts."""
    if "admin" not in session:
        return jsonify({"error": "unauthorized"}), 401
    days = int(request.args.get("days", 30))
    return jsonify(get_district_trends(days))


@app.route("/admin/api/village-risks")
def api_village_risks():
    """JSON endpoint for village heatmap data."""
    if "admin" not in session:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(get_village_risk_scores())


# ── Month 3: NHM CSV Export ───────────────────────────────────────
@app.route("/admin/export/nhm-csv")
def export_nhm_csv():
    """Export all patient data in NHM HMIS-compatible CSV format."""
    if "admin" not in session:
        return redirect("/admin/login")

    try:
        from sqlalchemy import text as sqlt
        with engine.connect() as conn:
            rows = conn.execute(sqlt("""
                SELECT
                    p.phone            AS mother_id,
                    p.name             AS mother_name,
                    p.village,
                    p.block_name,
                    p.district,
                    p.week             AS gestational_weeks,
                    p.status,
                    p.created_at::date AS registration_date,
                    aw.name            AS asha_name,
                    COUNT(DISTINCT ar.id)  AS anc_visits_done,
                    COUNT(DISTINCT aa.id)  AS total_alerts,
                    COUNT(DISTINCT CASE WHEN aa.status='Resolved'
                          THEN aa.id END) AS resolved_alerts,
                    MAX(aa.escalation_level) AS max_escalation_level,
                    d.delivery_date,
                    d.birth_weight,
                    d.delivery_mode,
                    d.facility
                FROM patients p
                LEFT JOIN asha_workers aw ON p.asha_id = aw.asha_id
                LEFT JOIN anc_records  ar ON ar.phone  = p.phone
                LEFT JOIN asha_alerts  aa ON aa.phone  = p.phone
                LEFT JOIN deliveries    d ON d.phone   = p.phone
                WHERE p.step = 'registered'
                GROUP BY
                    p.phone, p.name, p.village, p.block_name,
                    p.district, p.week, p.status, p.created_at,
                    aw.name, d.delivery_date, d.birth_weight,
                    d.delivery_mode, d.facility
                ORDER BY p.district, p.village, p.name
            """)).fetchall()

        import csv
        import io
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow([
            "Mother ID", "Name", "Village", "Block", "District",
            "Gestational Weeks", "Status", "Registration Date",
            "ASHA Name", "ANC Visits Done", "Total Alerts",
            "Resolved Alerts", "Max Escalation Level",
            "Delivery Date", "Birth Weight (kg)",
            "Delivery Mode", "Delivery Facility"
        ])
        for r in rows:
            cw.writerow([
                r.mother_id, r.mother_name, r.village or "",
                r.block_name or "", r.district or "",
                r.gestational_weeks or "", r.status or "",
                r.registration_date, r.asha_name or "",
                r.anc_visits_done, r.total_alerts,
                r.resolved_alerts, r.max_escalation_level or 0,
                r.delivery_date or "", r.birth_weight or "",
                r.delivery_mode or "", r.facility or ""
            ])

        month_str = datetime.now().strftime("%Y-%m")
        return Response(
            si.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition":
                    f"attachment; filename=MaaSakhi_NHM_Export_{month_str}.csv"
            }
        )
    except Exception as e:
        print(f"NHM export error: {e}")
        return redirect("/admin?tab=analytics")


# ── Month 3: Monthly PDF Report ──────────────────────────────────
@app.route("/admin/export/monthly-pdf")
def export_monthly_pdf():
    """Generate and download monthly PDF summary report."""
    if "admin" not in session:
        return redirect("/admin/login")
    try:
        from reports import generate_monthly_pdf
        pdf_bytes = generate_monthly_pdf()
        month_str = datetime.now().strftime("%Y-%m")
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition":
                    f"attachment; filename=MaaSakhi_Report_{month_str}.pdf"
            }
        )
    except Exception as e:
        print(f"PDF report error: {e}")
        return redirect("/admin?tab=analytics")


# ── Month 2: Cron endpoint — auto escalation ─────────────────────
@app.route("/cron/escalate")
def cron_escalate():
    """
    Called by Railway / cron every 15 minutes.
    Escalates alerts that have been Pending > 2 hours with no response.
    Secure this with a secret header in production.
    """
    cron_secret = os.environ.get("CRON_SECRET", "")
    if cron_secret and request.headers.get("X-Cron-Secret") != cron_secret:
        return jsonify({"error": "unauthorized"}), 401

    from escalation import run_escalation_check
    escalated = run_escalation_check()
    return jsonify({"escalated": escalated, "timestamp": datetime.now().isoformat()})


# ── Month 4: Cron endpoint — postpartum / immunization reminders ──
@app.route("/cron/reminders")
def cron_reminders():
    """
    Called daily. Sends PNC check-in reminders and immunization due alerts.
    """
    cron_secret = os.environ.get("CRON_SECRET", "")
    if cron_secret and request.headers.get("X-Cron-Secret") != cron_secret:
        return jsonify({"error": "unauthorized"}), 401

    from reminders import send_pnc_reminders, send_immunization_reminders
    pnc_sent  = send_pnc_reminders()
    imm_sent  = send_immunization_reminders()
    return jsonify({
        "pnc_reminders_sent":  pnc_sent,
        "imm_reminders_sent":  imm_sent,
        "timestamp":           datetime.now().isoformat()
    })


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
