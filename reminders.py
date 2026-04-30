# ─────────────────────────────────────────────────────────────────
# MaaSakhi — reminders.py
# Automated Reminder Engine (Month 4)
#
# Dispatches WhatsApp reminders via Twilio for:
#   • PNC check-ins (Day 1, 3, 7, 14, 42 after delivery)
#   • Immunization / vaccine due dates
#   • ANC visit reminders (pregnancy weeks 12, 16, 28, 36)
#   • Iron + Folic Acid compliance nudges
#   • Govt scheme eligibility notifications
#   • Weekly pregnancy tips
#
# Entry points:
#   send_pnc_reminders()          → returns int (count sent)
#   send_immunization_reminders() → returns int (count sent)
#   send_anc_reminders()          → returns int (count sent)
#   send_weekly_tips()            → returns int (count sent)
#   send_scheme_notifications()   → returns int (count sent)
#   run_all_reminders()           → runs all, returns summary dict
#
# Called by /cron/reminders route in app.py (daily, 8:00 AM IST)
# ─────────────────────────────────────────────────────────────────

import os
from datetime import datetime, date, timedelta
from twilio.rest import Client

TWILIO_ACCOUNT_SID   = os.environ.get("TWILIO_ACCOUNT_SID",   "")
TWILIO_AUTH_TOKEN    = os.environ.get("TWILIO_AUTH_TOKEN",     "")
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_SMS_FROM      = os.environ.get("TWILIO_SMS_FROM",       "")


# ─────────────────────────────────────────────────────────────────
# WHATSAPP / SMS DISPATCH
# ─────────────────────────────────────────────────────────────────

def _twilio():
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def _send_whatsapp(to: str, body: str) -> bool:
    """Send WhatsApp message. Returns True on success."""
    if not to:
        return False
    clean = to.replace("whatsapp:", "").strip()
    wa_to = f"whatsapp:{clean}"
    try:
        msg = _twilio().messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=wa_to,
            body=body
        )
        print(f"[reminders] WA sent → {wa_to} | SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"[reminders] WA error → {wa_to}: {e}")
        return _send_sms_fallback(clean, body)


def _send_sms_fallback(to: str, body: str) -> bool:
    """SMS fallback when WhatsApp fails."""
    if not TWILIO_SMS_FROM or not to:
        return False
    try:
        msg = _twilio().messages.create(
            from_=TWILIO_SMS_FROM,
            to=to,
            body=body[:1600]
        )
        print(f"[reminders] SMS fallback → {to} | SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"[reminders] SMS error → {to}: {e}")
        return False


def _log_reminder_sent(reminder_type: str, phone: str, message: str):
    """Persist a reminder record to DB so we don't resend today."""
    from database import engine
    if not engine:
        return
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            # Create table if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS reminder_log (
                    id            SERIAL PRIMARY KEY,
                    reminder_type TEXT,
                    phone         TEXT,
                    message_preview TEXT,
                    sent_at       TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                INSERT INTO reminder_log (reminder_type, phone, message_preview)
                VALUES (:rtype, :phone, :preview)
            """), {
                "rtype":   reminder_type,
                "phone":   phone,
                "preview": message[:120]
            })
            conn.commit()
    except Exception as e:
        print(f"[reminders] log error: {e}")


def _already_sent_today(reminder_type: str, phone: str) -> bool:
    """Returns True if this reminder type was already sent to this phone today."""
    from database import engine
    if not engine:
        return False
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            count = conn.execute(text("""
                SELECT COUNT(*) FROM reminder_log
                WHERE reminder_type = :rtype
                  AND phone         = :phone
                  AND DATE(sent_at) = CURRENT_DATE
            """), {"rtype": reminder_type, "phone": phone}).scalar()
            return (count or 0) > 0
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────
# 1. PNC REMINDERS
#    Sent to: (a) patient on due day  (b) ASHA worker on due day
# ─────────────────────────────────────────────────────────────────

def send_pnc_reminders() -> int:
    """
    Check all postpartum patients and send PNC day reminders.
    Returns count of reminders sent.
    """
    from database import engine
    if not engine:
        return 0
    from sqlalchemy import text
    from postpartum import (
        is_pnc_due_today, build_pnc_reminder,
        build_asha_pnc_alert, days_since_delivery,
    )

    sent = 0
    today = date.today()

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    p.phone, p.name, p.language, p.address, p.village,
                    d.delivery_date, d.birth_weight,
                    aw.phone        AS asha_phone,
                    aw.name         AS asha_name,
                    aw.asha_id,
                    COALESCE(p.maps_url, '') AS maps_url
                FROM patients p
                JOIN deliveries     d  ON d.phone   = p.phone
                JOIN asha_workers   aw ON aw.asha_id = p.asha_id
                WHERE p.status = 'postpartum'
                  AND aw.is_active = TRUE
            """)).fetchall()

    except Exception as e:
        print(f"[reminders] PNC query error: {e}")
        return 0

    for r in rows:
        dd_str = r.delivery_date or ""
        if not dd_str:
            continue

        due, pnc_day = is_pnc_due_today(dd_str)
        if not due or pnc_day is None:
            continue

        # ── Send to patient ───────────────────────────────────────
        patient_key = f"pnc_patient_day{pnc_day}"
        if not _already_sent_today(patient_key, r.phone):
            msg = build_pnc_reminder(
                patient_name      = r.name,
                pnc_day           = pnc_day,
                delivery_date_str = dd_str,
                language          = r.language or "Hindi",
                include_asha_name = r.asha_name,
            )
            if _send_whatsapp(r.phone, msg):
                _log_reminder_sent(patient_key, r.phone, msg)
                sent += 1

        # ── Send to ASHA worker ───────────────────────────────────
        asha_key = f"pnc_asha_day{pnc_day}"
        if r.asha_phone and not _already_sent_today(asha_key, r.asha_phone):
            asha_msg = build_asha_pnc_alert(
                patient_name   = r.name,
                patient_phone  = r.phone,
                patient_address= r.address or r.village or "Not provided",
                pnc_day        = pnc_day,
                delivery_date_str = dd_str,
                birth_weight   = r.birth_weight or "",
                maps_link      = r.maps_url or "",
            )
            if _send_whatsapp(r.asha_phone, asha_msg):
                _log_reminder_sent(asha_key, r.asha_phone, asha_msg)
                sent += 1

    print(f"[reminders] PNC — {sent} messages sent")
    return sent


# ─────────────────────────────────────────────────────────────────
# 2. IMMUNIZATION REMINDERS
#    Sent 3 days before vaccine due date + on due date
# ─────────────────────────────────────────────────────────────────

def send_immunization_reminders() -> int:
    """
    Check all children and send vaccine reminders.
    Sends:
      - 3 days before due date: advance notice to mother
      - On due date: reminder + ASHA alert
      - Overdue (3–7 days past): urgent follow-up to ASHA
    Returns count sent.
    """
    from database import engine, get_children, get_immunization_records
    if not engine:
        return 0
    from sqlalchemy import text
    from child_health import (
        get_immunization_schedule, mark_given_vaccines,
        build_vaccine_reminder, build_overdue_vaccine_asha_alert,
    )

    sent  = 0
    today = date.today()

    try:
        with engine.connect() as conn:
            # All children with mother + ASHA info
            rows = conn.execute(text("""
                SELECT
                    c.id, c.child_name, c.dob, c.gender, c.mother_phone,
                    p.name         AS mother_name,
                    p.language,
                    aw.phone       AS asha_phone,
                    aw.name        AS asha_name
                FROM children c
                LEFT JOIN patients     p  ON p.phone   = c.mother_phone
                LEFT JOIN asha_workers aw ON aw.asha_id = c.asha_id
                WHERE aw.is_active = TRUE OR aw.asha_id IS NULL
            """)).fetchall()
    except Exception as e:
        print(f"[reminders] immunization query error: {e}")
        return 0

    for r in rows:
        if not r.dob:
            continue

        given    = {v["vaccine_name"] for v in get_immunization_records(r.id)}
        schedule = get_immunization_schedule(r.dob)
        schedule = mark_given_vaccines(schedule, given)

        for item in schedule:
            if item["status"] == "given":
                continue

            days_away = item["days_away"]

            # ── 3-day advance notice to mother ────────────────────
            if days_away == 3:
                key = f"vax_advance_{item['vaccine']}_{r.id}"
                if not _already_sent_today(key, r.mother_phone):
                    msg = build_vaccine_reminder(
                        mother_name  = r.mother_name or "Aap",
                        child_name   = r.child_name,
                        vaccines_due = [item],
                        language     = r.language or "Hindi",
                        asha_name    = r.asha_name or "",
                    )
                    if _send_whatsapp(r.mother_phone, msg):
                        _log_reminder_sent(key, r.mother_phone, msg)
                        sent += 1

            # ── Due today: mother + ASHA ──────────────────────────
            elif abs(days_away) <= 1:
                # Mother reminder
                key_m = f"vax_due_{item['vaccine']}_{r.id}"
                if not _already_sent_today(key_m, r.mother_phone):
                    msg = build_vaccine_reminder(
                        mother_name  = r.mother_name or "Aap",
                        child_name   = r.child_name,
                        vaccines_due = [item],
                        language     = r.language or "Hindi",
                        asha_name    = r.asha_name or "",
                    )
                    if _send_whatsapp(r.mother_phone, msg):
                        _log_reminder_sent(key_m, r.mother_phone, msg)
                        sent += 1

                # ASHA alert
                if r.asha_phone:
                    key_a = f"vax_asha_due_{item['vaccine']}_{r.id}"
                    if not _already_sent_today(key_a, r.asha_phone):
                        asha_msg = (
                            f"💉 *Vaccine Due Today*\n\n"
                            f"Child: {r.child_name}\n"
                            f"Mother: {r.mother_name} ({r.mother_phone})\n"
                            f"Vaccine: {item['label']}\n"
                            f"Where: {item['given_at']}\n\n"
                            f"Please accompany or remind family today. 💚"
                        )
                        if _send_whatsapp(r.asha_phone, asha_msg):
                            _log_reminder_sent(key_a, r.asha_phone, asha_msg)
                            sent += 1

            # ── 3–7 days overdue: urgent ASHA follow-up ───────────
            elif -7 <= days_away < -1:
                if r.asha_phone:
                    key_o = f"vax_overdue_{item['vaccine']}_{r.id}"
                    if not _already_sent_today(key_o, r.asha_phone):
                        overdue_msg = build_overdue_vaccine_asha_alert(
                            mother_name  = r.mother_name or "Patient",
                            mother_phone = r.mother_phone,
                            child_name   = r.child_name,
                            overdue      = [item],
                        )
                        if _send_whatsapp(r.asha_phone, overdue_msg):
                            _log_reminder_sent(key_o, r.asha_phone, overdue_msg)
                            sent += 1

    print(f"[reminders] Immunization — {sent} messages sent")
    return sent


# ─────────────────────────────────────────────────────────────────
# 3. ANC VISIT REMINDERS
#    Sent to patient + ASHA when ANC is due based on gestational week
# ─────────────────────────────────────────────────────────────────

# (min_week, max_week, anc_number, message_hi, message_en)
ANC_REMINDERS = [
    (
        10, 12, 1,
        (
            "🌸 *ANC 1 Check-up Due!*\n\n"
            "Namaste! Aap 10–12 hafte ki pregnant hain.\n"
            "Pehli ANC check-up bahut zaroori hai:\n\n"
            "🩺 Blood pressure + weight check\n"
            "🧪 Blood tests (Hb, Blood Group, HIV, Syphilis)\n"
            "💊 Iron + Folic Acid tablets shuru karein\n"
            "🔬 Urine test\n\n"
            "Apni ASHA worker se appointment le lein. 💚"
        ),
        (
            "🌸 *ANC 1 Check-up Due!*\n\n"
            "Hello! You are 10–12 weeks pregnant.\n"
            "Your first ANC check-up is very important:\n\n"
            "🩺 Blood pressure + weight check\n"
            "🧪 Blood tests (Hb, Blood Group, HIV, Syphilis)\n"
            "💊 Start Iron + Folic Acid tablets\n"
            "🔬 Urine test\n\n"
            "Ask your ASHA worker to arrange an appointment. 💚"
        ),
    ),
    (
        14, 16, 2,
        (
            "🌸 *ANC 2 Check-up Due!*\n\n"
            "Aap 14–16 hafte ki pregnant hain.\n"
            "Doosri ANC check-up mein:\n\n"
            "⚖️ Vajan check\n"
            "💊 Iron + Calcium tablets ka review\n"
            "🤰 Baby ki heartbeat sunna\n"
            "🩸 Anaemia check\n\n"
            "Apni ASHA worker ko iske baare mein batayein. 💚"
        ),
        (
            "🌸 *ANC 2 Check-up Due!*\n\n"
            "You are 14–16 weeks pregnant.\n"
            "Second ANC check-up includes:\n\n"
            "⚖️ Weight measurement\n"
            "💊 Iron + Calcium tablet review\n"
            "🤰 Baby's heartbeat check\n"
            "🩸 Anaemia check\n\n"
            "Inform your ASHA worker. 💚"
        ),
    ),
    (
        28, 32, 3,
        (
            "🌸 *ANC 3 Check-up Due!*\n\n"
            "Aap 28–32 hafte ki pregnant hain.\n"
            "Teesri ANC check-up bahut zaroori hai:\n\n"
            "🩺 BP check — pre-eclampsia ke liye\n"
            "⚖️ Baby ka vikas check karna\n"
            "💉 TT vaccine (agar baaki ho)\n"
            "🩸 Haemoglobin check\n"
            "🏥 Delivery plan banayein\n\n"
            "PHC ya ASHA worker se sampark karein. 💚"
        ),
        (
            "🌸 *ANC 3 Check-up Due!*\n\n"
            "You are 28–32 weeks pregnant.\n"
            "Third ANC check-up is important:\n\n"
            "🩺 BP check — watch for pre-eclampsia\n"
            "⚖️ Baby growth assessment\n"
            "💉 TT vaccine if pending\n"
            "🩸 Haemoglobin check\n"
            "🏥 Make your delivery plan\n\n"
            "Contact your PHC or ASHA worker. 💚"
        ),
    ),
    (
        36, 38, 4,
        (
            "🌸 *ANC 4 — Final Check-up Due!*\n\n"
            "Aap 36–38 hafte ki pregnant hain.\n"
            "Yeh aakhri ANC check-up bahut zaroori hai:\n\n"
            "🏥 Delivery ki jagah decide karein\n"
            "🚑 Emergency transport plan banayein\n"
            "🩺 Baby ki position check karein\n"
            "📋 Birth preparedness — kya lena hai, kahan jaana hai\n"
            "💊 Zyada Iron + Calcium tablets lein\n\n"
            "Apni ASHA worker ke saath poora plan banayein. 💚"
        ),
        (
            "🌸 *ANC 4 — Final Check-up Due!*\n\n"
            "You are 36–38 weeks pregnant.\n"
            "This final ANC is very important:\n\n"
            "🏥 Confirm delivery location\n"
            "🚑 Arrange emergency transport\n"
            "🩺 Check baby's position\n"
            "📋 Birth preparedness plan\n"
            "💊 Continue Iron + Calcium tablets\n\n"
            "Make a complete plan with your ASHA worker. 💚"
        ),
    ),
]


def send_anc_reminders() -> int:
    """
    Send ANC check-up reminders to patients whose gestational week
    falls within each ANC window.
    Returns count sent.
    """
    from database import engine
    if not engine:
        return 0
    from sqlalchemy import text

    sent = 0

    try:
        with engine.connect() as conn:
            patients = conn.execute(text("""
                SELECT
                    p.phone, p.name, p.week, p.language,
                    aw.phone  AS asha_phone,
                    aw.name   AS asha_name
                FROM patients p
                LEFT JOIN asha_workers aw ON aw.asha_id = p.asha_id
                WHERE p.step   = 'registered'
                  AND p.status = 'active'
                  AND p.week   IS NOT NULL
            """)).fetchall()
    except Exception as e:
        print(f"[reminders] ANC query error: {e}")
        return 0

    for r in patients:
        if r.week is None:
            continue
        lang_key = "en" if (r.language or "").lower() in ("english", "en") else "hi"

        for min_w, max_w, anc_num, msg_hi, msg_en in ANC_REMINDERS:
            if min_w <= r.week <= max_w:
                key = f"anc_{anc_num}_reminder"
                if _already_sent_today(key, r.phone):
                    continue

                msg = msg_en if lang_key == "en" else msg_hi
                if r.asha_name:
                    if lang_key == "hi":
                        msg += f"\n\n👩 Aapki ASHA worker: *{r.asha_name}*"
                    else:
                        msg += f"\n\n👩 Your ASHA worker: *{r.asha_name}*"

                if _send_whatsapp(r.phone, msg):
                    _log_reminder_sent(key, r.phone, msg)
                    sent += 1

                # Alert ASHA worker too
                if r.asha_phone:
                    asha_key = f"anc_{anc_num}_asha_alert"
                    if not _already_sent_today(asha_key, r.asha_phone):
                        asha_msg = (
                            f"📋 *ANC {anc_num} Reminder Sent*\n\n"
                            f"Patient: {r.name} ({r.phone})\n"
                            f"Current week: {r.week}\n\n"
                            f"Please schedule ANC {anc_num} visit. 💚"
                        )
                        if _send_whatsapp(r.asha_phone, asha_msg):
                            _log_reminder_sent(asha_key, r.asha_phone, asha_msg)
                            sent += 1

    print(f"[reminders] ANC — {sent} messages sent")
    return sent


# ─────────────────────────────────────────────────────────────────
# 4. WEEKLY PREGNANCY TIPS
#    Sent every Monday to all active registered patients
# ─────────────────────────────────────────────────────────────────

WEEKLY_TIPS = {
    # week: (tip_hi, tip_en)
    "early": (   # weeks 1–12
        "🌸 *Pehli Timahi — Pehle 12 Hafte*\n\n"
        "💊 Folic Acid 400mcg roz lein — bachche ke brain ke liye\n"
        "🤢 Ulti ya ji machlana normal hai — thoda thoda khaayein\n"
        "☕ Chai/coffee kam karein (200mg caffeine se kam)\n"
        "🚫 Smoking aur sharaab bilkul nahi\n"
        "😴 Zyada neend zaroor lein\n\n"
        "Koi bhi takleef ho toh batayein. 💚",
        "🌸 *First Trimester — Weeks 1–12*\n\n"
        "💊 Take Folic Acid 400mcg daily — for baby's brain\n"
        "🤢 Nausea is normal — eat small frequent meals\n"
        "☕ Limit tea/coffee (under 200mg caffeine)\n"
        "🚫 No smoking or alcohol\n"
        "😴 Rest as much as you can\n\nMessage me anytime. 💚"
    ),
    "mid": (     # weeks 13–28
        "🌸 *Doosri Timahi — Hafte 13–28*\n\n"
        "🤰 Baby ab hilna shuru karta hai — isko feel karein\n"
        "🥗 Iron se bhari cheezein khaayein: palak, dal, anday\n"
        "🦷 Daant ka dhyan rakhein — muh ki sehat zaroori hai\n"
        "🚰 Roz 8–10 glass paani piyen\n"
        "🧘 Halki kasrat — walk karna accha hai\n"
        "📋 ANC 2 aur ANC 3 miss mat karein!\n\n"
        "Hamesha aapke saath hoon. 💚",
        "🌸 *Second Trimester — Weeks 13–28*\n\n"
        "🤰 Baby starts moving — enjoy those kicks!\n"
        "🥗 Eat iron-rich foods: spinach, lentils, eggs\n"
        "🦷 Take care of your teeth — oral health matters\n"
        "🚰 Drink 8–10 glasses of water daily\n"
        "🧘 Light exercise — walking is great\n"
        "📋 Don't miss ANC 2 and ANC 3!\n\nAlways here for you. 💚"
    ),
    "late": (    # weeks 29–40
        "🌸 *Teesri Timahi — Hafte 29–40*\n\n"
        "🏥 Delivery ka plan abhi se banayein\n"
        "🚑 Emergency transport ka number save karein: 108\n"
        "🛏 Seedha letne ke bajaye left side par leten\n"
        "⚠️ Agar bahut zyada sujan, sir dard ya aankhon ke aage andhere ho — "
        "turant ASHA worker ko call karein\n"
        "💊 Iron + Calcium tablets zyada zaroor lein\n"
        "📦 Hospital bag pack kar lein\n\n"
        "Aap bilkul theek kar rahi hain! 💚",
        "🌸 *Third Trimester — Weeks 29–40*\n\n"
        "🏥 Make your delivery plan now\n"
        "🚑 Save emergency transport: 108\n"
        "🛏 Sleep on your left side\n"
        "⚠️ Severe swelling, headache or visual changes — "
        "call your ASHA worker immediately\n"
        "💊 Take extra Iron + Calcium tablets\n"
        "📦 Pack your hospital bag\n\nYou are doing great! 💚"
    ),
}


def send_weekly_tips() -> int:
    """
    Send a weekly pregnancy tip to all active patients.
    Only runs on Mondays (weekday == 0). Returns count sent.
    """
    if date.today().weekday() != 0:   # Monday only
        print("[reminders] Weekly tips — skipped (not Monday)")
        return 0

    from database import engine
    if not engine:
        return 0
    from sqlalchemy import text

    sent = 0

    try:
        with engine.connect() as conn:
            patients = conn.execute(text("""
                SELECT phone, name, week, language
                FROM patients
                WHERE step='registered' AND status='active' AND week IS NOT NULL
            """)).fetchall()
    except Exception as e:
        print(f"[reminders] weekly tips query error: {e}")
        return 0

    for r in patients:
        week     = r.week or 0
        lang_key = "en" if (r.language or "").lower() in ("english", "en") else "hi"
        idx      = 0 if lang_key == "hi" else 1

        if week <= 12:
            tip = WEEKLY_TIPS["early"][idx]
        elif week <= 28:
            tip = WEEKLY_TIPS["mid"][idx]
        else:
            tip = WEEKLY_TIPS["late"][idx]

        greeting = (
            f"Namaste {r.name}! 🌸\n\n"
            if lang_key == "hi" else
            f"Hello {r.name}! 🌸\n\n"
        )
        week_line = (
            f"Aap hafte {week} mein hain.\n\n"
            if lang_key == "hi" else
            f"You are in week {week}.\n\n"
        )
        msg = greeting + week_line + tip

        key = "weekly_tip"
        if not _already_sent_today(key, r.phone):
            if _send_whatsapp(r.phone, msg):
                _log_reminder_sent(key, r.phone, msg)
                sent += 1

    print(f"[reminders] Weekly tips — {sent} messages sent")
    return sent


# ─────────────────────────────────────────────────────────────────
# 5. GOVT SCHEME NOTIFICATIONS
#    Sends once when patient crosses eligibility milestone
# ─────────────────────────────────────────────────────────────────

SCHEME_TRIGGERS = [
    # (week_threshold, scheme_name, message_hi, message_en)
    (
        12,
        "PMMVY",
        (
            "🏛️ *PM Matru Vandana Yojana — Aap Eligible Hain!*\n\n"
            "Pehle zinda bachche ke liye sarkar ₹5,000 deti hai — "
            "3 kiston mein.\n\n"
            "📝 *Abhi karo:*\n"
            "Form 1-A bharo — Anganwadi ya Health Centre mein\n"
            "Bank account + Aadhaar + MCP card le jaayein\n\n"
            "Apni ASHA worker se madad lein. 💚"
        ),
        (
            "🏛️ *PM Matru Vandana Yojana — You Are Eligible!*\n\n"
            "The government provides ₹5,000 for your first living child "
            "— in 3 instalments.\n\n"
            "📝 *Apply now:*\n"
            "Fill Form 1-A at Anganwadi or Health Centre\n"
            "Bring bank account + Aadhaar + MCP card\n\n"
            "Ask your ASHA worker for help. 💚"
        ),
    ),
    (
        8,
        "JSY",
        (
            "🏛️ *Janani Suraksha Yojana (JSY)*\n\n"
            "Government hospital mein delivery par ₹1,400 milte hain "
            "(rural area).\n\n"
            "✅ Sarkari hospital mein delivery karwayein\n"
            "✅ Discharge ke time cash milega\n"
            "✅ Aapki ASHA worker ko bhi ₹600 incentive milega\n\n"
            "Apni ASHA worker se poori jankari lein. 💚"
        ),
        (
            "🏛️ *Janani Suraksha Yojana (JSY)*\n\n"
            "₹1,400 cash benefit for institutional delivery in a "
            "government hospital (rural).\n\n"
            "✅ Deliver at a government hospital\n"
            "✅ Cash given at discharge\n"
            "✅ Your ASHA worker also gets ₹600 incentive\n\n"
            "Ask your ASHA worker for full details. 💚"
        ),
    ),
    (
        6,
        "JSSK",
        (
            "🏛️ *Janani Shishu Suraksha Karyakram (JSSK)*\n\n"
            "Sarkari hospital mein FREE milta hai:\n"
            "🆓 Delivery (normal ya C-section)\n"
            "🆓 Dawaiyaan aur tests\n"
            "🆓 Khana (3 din)\n"
            "🆓 Khoon (zarurat padne par)\n"
            "🆓 Transport (ghar se hospital aur wapas)\n\n"
            "Koi paise mat dena! Yeh aapka haq hai. 💚"
        ),
        (
            "🏛️ *Janani Shishu Suraksha Karyakram (JSSK)*\n\n"
            "You are entitled to FREE services at government hospitals:\n"
            "🆓 Delivery (normal or C-section)\n"
            "🆓 Medicines and tests\n"
            "🆓 Food (3 days)\n"
            "🆓 Blood (if needed)\n"
            "🆓 Transport (home to hospital and back)\n\n"
            "Demand your rights — it's free! 💚"
        ),
    ),
]


def send_scheme_notifications() -> int:
    """
    Send govt scheme eligibility notifications to patients who have
    just crossed the gestational week threshold for each scheme.
    Sent only once per scheme per patient.
    Returns count sent.
    """
    from database import engine
    if not engine:
        return 0
    from sqlalchemy import text

    sent = 0

    try:
        with engine.connect() as conn:
            patients = conn.execute(text("""
                SELECT phone, name, week, language
                FROM patients
                WHERE step='registered' AND status='active' AND week IS NOT NULL
            """)).fetchall()
    except Exception as e:
        print(f"[reminders] scheme notifications query error: {e}")
        return 0

    for r in patients:
        week     = r.week or 0
        lang_key = "en" if (r.language or "").lower() in ("english", "en") else "hi"
        idx      = 1 if lang_key == "en" else 0

        for threshold, scheme, msg_hi, msg_en in SCHEME_TRIGGERS:
            if week < threshold:
                continue

            key = f"scheme_{scheme}_notif"
            if _already_sent_today(key, r.phone):
                continue

            # Check if we ever sent this scheme notification before
            # (not just today — use a lifetime check)
            from database import engine as db_eng
            if db_eng:
                try:
                    from sqlalchemy import text as sqlt
                    with db_eng.connect() as conn2:
                        count = conn2.execute(sqlt("""
                            SELECT COUNT(*) FROM reminder_log
                            WHERE reminder_type = :rtype AND phone = :phone
                        """), {"rtype": key, "phone": r.phone}).scalar()
                        if (count or 0) > 0:
                            continue     # already sent before, skip
                except Exception:
                    pass

            msg = msg_en if lang_key == "en" else msg_hi
            greeting = f"Namaste {r.name}! " if lang_key == "hi" else f"Hello {r.name}! "
            full_msg = greeting + "\n\n" + msg

            if _send_whatsapp(r.phone, full_msg):
                _log_reminder_sent(key, r.phone, full_msg)
                sent += 1

    print(f"[reminders] Scheme notifications — {sent} messages sent")
    return sent


# ─────────────────────────────────────────────────────────────────
# 6. IRON TABLET COMPLIANCE NUDGE
#    Sent on Day 7 and Day 30 after registration if no GREEN symptom log
# ─────────────────────────────────────────────────────────────────

def send_iron_reminders() -> int:
    """
    Send iron + folic acid compliance reminders.
    Targets patients who registered 7 or 30 days ago and
    have had no symptom activity (may have dropped off).
    Returns count sent.
    """
    from database import engine
    if not engine:
        return 0
    from sqlalchemy import text

    sent  = 0
    today = date.today()

    try:
        with engine.connect() as conn:
            # Patients registered exactly 7 or 30 days ago
            patients = conn.execute(text("""
                SELECT p.phone, p.name, p.week, p.language
                FROM patients p
                WHERE p.step   = 'registered'
                  AND p.status = 'active'
                  AND (
                    DATE(p.created_at) = :day7
                    OR DATE(p.created_at) = :day30
                  )
            """), {
                "day7":  today - timedelta(days=7),
                "day30": today - timedelta(days=30),
            }).fetchall()
    except Exception as e:
        print(f"[reminders] iron reminder query error: {e}")
        return 0

    for r in patients:
        lang_key = "en" if (r.language or "").lower() in ("english", "en") else "hi"
        key      = "iron_reminder"

        if _already_sent_today(key, r.phone):
            continue

        if lang_key == "hi":
            msg = (
                f"🌸 Namaste {r.name}!\n\n"
                "💊 *Iron + Folic Acid Tablet Yaad Dilana*\n\n"
                "Roz ek tablet zaroor lein — khane ke baad.\n\n"
                "Fayde:\n"
                "🩸 Khoon ki kami (anaemia) door karta hai\n"
                "🧠 Baby ka dimag achha banta hai\n"
                "😴 Thakaan kam hoti hai\n\n"
                "Tablet khatam ho toh ASHA worker ya PHC se lein. 💚"
            )
        else:
            msg = (
                f"🌸 Hello {r.name}!\n\n"
                "💊 *Iron + Folic Acid Tablet Reminder*\n\n"
                "Take one tablet daily — after meals.\n\n"
                "Why it matters:\n"
                "🩸 Prevents anaemia (blood deficiency)\n"
                "🧠 Supports baby's brain development\n"
                "😴 Reduces fatigue\n\n"
                "Ask your ASHA worker or PHC if you need more tablets. 💚"
            )

        if _send_whatsapp(r.phone, msg):
            _log_reminder_sent(key, r.phone, msg)
            sent += 1

    print(f"[reminders] Iron reminders — {sent} messages sent")
    return sent


# ─────────────────────────────────────────────────────────────────
# 7. POSTPARTUM DEPRESSION SCREENING REMINDER
#    Sent at Day 14 and Day 42 post-delivery
# ─────────────────────────────────────────────────────────────────

def send_ppd_screening_reminders() -> int:
    """
    Send Edinburgh Postnatal Depression Scale mini-check reminders
    to postpartum mothers at Day 14 and Day 42.
    Returns count sent.
    """
    from database import engine
    if not engine:
        return 0
    from sqlalchemy import text
    from postpartum import days_since_delivery

    sent = 0

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT p.phone, p.name, p.language,
                       d.delivery_date
                FROM patients p
                JOIN deliveries d ON d.phone = p.phone
                WHERE p.status = 'postpartum'
            """)).fetchall()
    except Exception as e:
        print(f"[reminders] PPD screening query error: {e}")
        return 0

    for r in rows:
        days_pp = days_since_delivery(r.delivery_date or "")
        if days_pp is None:
            continue

        if days_pp not in (14, 42):
            continue

        lang_key = "en" if (r.language or "").lower() in ("english", "en") else "hi"
        key      = f"ppd_screen_day{days_pp}"

        if _already_sent_today(key, r.phone):
            continue

        if lang_key == "hi":
            msg = (
                f"🌸 Namaste {r.name}!\n\n"
                "💜 *Aapki Manostithi Kaisi Hai?*\n\n"
                "Delivery ke baad kuch maaon ko udaasi ya anxiety hoti hai — "
                "yeh bilkul normal hai.\n\n"
                "Kya aap pichle hafte mein in mein se kuch feel kar rahi hain?\n"
                "• Bahut udaas ya rone ka mann\n"
                "• Baby ke baare mein darr ya chinta\n"
                "• Khud ko hurt karne ke khayal\n\n"
                "Agar haan — please apni ASHA worker ya doctor ko batayein.\n"
                "Aap akeli nahi hain. Help available hai. 💚"
            )
        else:
            msg = (
                f"🌸 Hello {r.name}!\n\n"
                "💜 *How Are You Feeling?*\n\n"
                "Some mothers experience sadness or anxiety after delivery — "
                "this is very common.\n\n"
                "Have you felt any of these in the past week?\n"
                "• Feeling very sad or tearful\n"
                "• Excessive worry or anxiety about baby\n"
                "• Thoughts of harming yourself\n\n"
                "If yes — please tell your ASHA worker or doctor.\n"
                "You are not alone. Help is available. 💚"
            )

        if _send_whatsapp(r.phone, msg):
            _log_reminder_sent(key, r.phone, msg)
            sent += 1

    print(f"[reminders] PPD screening — {sent} messages sent")
    return sent


# ─────────────────────────────────────────────────────────────────
# 8. DEWORMING REMINDERS
#    Twice yearly — February and August (National Deworming Day)
# ─────────────────────────────────────────────────────────────────

def send_deworming_reminders() -> int:
    """
    Send deworming reminders to eligible children's mothers.
    Only runs in February and August (NDD months).
    Returns count sent.
    """
    today = date.today()
    if today.month not in (2, 8):
        return 0

    # Only send on the 1st of the deworming month
    if today.day != 1:
        return 0

    from database import engine
    if not engine:
        return 0
    from sqlalchemy import text
    from child_health import is_deworming_due

    sent = 0

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT c.id, c.child_name, c.dob, c.mother_phone,
                       p.name AS mother_name, p.language
                FROM children c
                LEFT JOIN patients p ON p.phone = c.mother_phone
            """)).fetchall()
    except Exception as e:
        print(f"[reminders] deworming query error: {e}")
        return 0

    for r in rows:
        if not is_deworming_due(r.dob or ""):
            continue

        lang_key = "en" if (r.language or "").lower() in ("english", "en") else "hi"
        key      = f"deworming_{today.year}_{today.month}"

        if _already_sent_today(key, r.mother_phone):
            continue

        if lang_key == "hi":
            msg = (
                f"💊 Namaste {r.mother_name}!\n\n"
                f"*{r.child_name} ke liye Deworming Tablet*\n\n"
                f"Aaj National Deworming Day hai.\n"
                f"{r.child_name} (1–5 saal) ko Albendazole 400mg tablet "
                f"deni chahiye.\n\n"
                f"📍 Nearest Anganwadi ya PHC jaayein.\n"
                f"✅ Tablet free mein milti hai.\n\n"
                f"Pet ke keede nikalna zaroor hai — poshan ke liye. 💚"
            )
        else:
            msg = (
                f"💊 Hello {r.mother_name}!\n\n"
                f"*Deworming Tablet for {r.child_name}*\n\n"
                f"Today is National Deworming Day.\n"
                f"{r.child_name} (1–5 years) should receive Albendazole 400mg.\n\n"
                f"📍 Visit your nearest Anganwadi or PHC.\n"
                f"✅ The tablet is free of cost.\n\n"
                f"Deworming improves nutrition absorption. 💚"
            )

        if _send_whatsapp(r.mother_phone, msg):
            _log_reminder_sent(key, r.mother_phone, msg)
            sent += 1

    print(f"[reminders] Deworming — {sent} messages sent")
    return sent


# ─────────────────────────────────────────────────────────────────
# RUN ALL REMINDERS — single entry point for /cron/reminders
# ─────────────────────────────────────────────────────────────────

def run_all_reminders() -> dict:
    """
    Run every reminder function in sequence.
    Returns a summary dict for the cron response.

    Called by app.py:
        from reminders import run_all_reminders
        result = run_all_reminders()
    """
    print(f"[reminders] Starting full reminder run — {datetime.now()}")

    summary = {
        "timestamp":        datetime.now().isoformat(),
        "pnc_sent":         0,
        "immunization_sent":0,
        "anc_sent":         0,
        "weekly_tips_sent": 0,
        "scheme_sent":      0,
        "iron_sent":        0,
        "ppd_sent":         0,
        "deworming_sent":   0,
        "total_sent":       0,
        "errors":           [],
    }

    tasks = [
        ("pnc_sent",          send_pnc_reminders),
        ("immunization_sent", send_immunization_reminders),
        ("anc_sent",          send_anc_reminders),
        ("weekly_tips_sent",  send_weekly_tips),
        ("scheme_sent",       send_scheme_notifications),
        ("iron_sent",         send_iron_reminders),
        ("ppd_sent",          send_ppd_screening_reminders),
        ("deworming_sent",    send_deworming_reminders),
    ]

    for key, fn in tasks:
        try:
            summary[key] = fn()
        except Exception as e:
            msg = f"{fn.__name__}: {e}"
            print(f"[reminders] ERROR — {msg}")
            summary["errors"].append(msg)
            summary[key] = 0

    summary["total_sent"] = sum(
        summary[k] for k in summary
        if k.endswith("_sent") and k != "total_sent"
    )

    print(
        f"[reminders] Run complete — "
        f"{summary['total_sent']} total messages sent"
    )
    return summary


# ─────────────────────────────────────────────────────────────────
# SELF-TEST  (python reminders.py)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== reminders.py self-test (dry run — no messages sent) ===\n")

    # Patch _send_whatsapp to not actually send
    import reminders as _self
    _sent_log = []

    def _dry_send(to, body):
        _sent_log.append({"to": to, "preview": body[:60]})
        return True

    _self._send_whatsapp = _dry_send

    result = run_all_reminders()

    print(f"\nSummary:")
    for k, v in result.items():
        if k not in ("errors", "timestamp"):
            print(f"  {k:<25} {v}")

    if result["errors"]:
        print(f"\nErrors:")
        for e in result["errors"]:
            print(f"  ✗ {e}")

    print(f"\nDry-run complete. {len(_sent_log)} messages would have been sent.")