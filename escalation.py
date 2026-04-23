# ─────────────────────────────────────────────────────────────────
# MaaSakhi Escalation Engine
# Auto-escalates unresponded alerts up the hierarchy
#
# Timeline:
# 0 min  → Alert sent to ASHA worker
# 2 hrs  → No response → Escalate to SUPERVISOR
# 4 hrs  → No response → Escalate to BMO
# 6 hrs  → No response → Escalate to DHO/Admin
# ─────────────────────────────────────────────────────────────────

import os
import threading
import time
from datetime import datetime, timedelta
from twilio.rest import Client
from sqlalchemy import text

TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
DHO_PHONE              = os.environ.get("DHO_PHONE", "")

# How many hours before escalating to next level
ESCALATION_HOURS = {
    0: 2,   # ASHA not responded in 2 hrs → go to Supervisor
    1: 4,   # Supervisor not responded in 4 hrs → go to BMO
    2: 6,   # BMO not responded in 6 hrs → go to DHO
}


# ─────────────────────────────────────────────────────────────────
# SEND WHATSAPP — core helper
# ─────────────────────────────────────────────────────────────────

def send_whatsapp(to_phone, message):
    """Send WhatsApp message via Twilio."""
    try:
        if not to_phone:
            print("No phone number — skipping WhatsApp")
            return False

        # Ensure whatsapp: prefix
        if not to_phone.startswith("whatsapp:"):
            to_phone = "whatsapp:" + to_phone

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_phone,
            body=message
        )
        print(f"WhatsApp sent to {to_phone} — SID: {msg.sid}")
        return True

    except Exception as e:
        print(f"WhatsApp send error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────
# ESCALATION MESSAGES — per level
# ─────────────────────────────────────────────────────────────────

def build_escalation_message(alert, level, role_name):
    """
    Builds the WhatsApp escalation message for each hierarchy level.
    level 1 = Supervisor, level 2 = BMO, level 3 = DHO
    """
    maps_line = (
        f"\n📌 Navigate to patient:\n{alert['maps_link']}"
        if alert.get("maps_link") else ""
    )

    hours_passed = level * 2

    headers = {
        1: "⚠️ ESCALATION — ASHA Worker Not Responded",
        2: "🔴 URGENT ESCALATION — Supervisor Not Responded",
        3: "🚨 CRITICAL ESCALATION — BMO Not Responded"
    }

    intros = {
        1: (
            f"This alert was sent to ASHA worker {alert.get('asha_name', '')} "
            f"{hours_passed} hours ago but has NOT been attended.\n"
            f"Please contact the ASHA worker or visit the patient directly."
        ),
        2: (
            f"This alert was escalated to the Supervisor {hours_passed - 2} hours ago "
            f"but is still unresolved.\n"
            f"Immediate intervention required at block level."
        ),
        3: (
            f"This alert has been escalating for {hours_passed} hours with no resolution.\n"
            f"CRITICAL: District-level intervention required immediately."
        )
    }

    return (
        f"{headers.get(level, '🚨 ESCALATION ALERT')}\n\n"
        f"Patient: {alert['name']}\n"
        f"Pregnancy Week: {alert['week']}\n"
        f"Symptom: {alert['symptom']}\n"
        f"Phone: {alert['phone']}\n"
        f"Village: {alert.get('village', 'Not provided')}\n"
        f"Address: {alert.get('address', 'Not provided')}\n"
        f"Original Alert Time: {alert.get('created_at', '').strftime('%d %b %Y, %I:%M %p') if hasattr(alert.get('created_at', ''), 'strftime') else ''}\n"
        f"{maps_line}\n\n"
        f"{intros.get(level, '')}\n\n"
        f"— MaaSakhi Escalation System"
    )


# ─────────────────────────────────────────────────────────────────
# GET CONTACT PHONE — for each level
# ─────────────────────────────────────────────────────────────────

def get_escalation_phone(alert, target_level, engine):
    """
    Returns the phone number to escalate to based on target level.
    level 1 = Supervisor, level 2 = BMO, level 3 = DHO
    """
    try:
        with engine.connect() as conn:

            if target_level == 1:
                # Escalate to ASHA Supervisor
                supervisor_id = alert.get("supervisor_id", "")
                if not supervisor_id:
                    # Try to find supervisor via ASHA worker
                    result = conn.execute(
                        text("""
                            SELECT s.phone, s.name
                            FROM asha_supervisors s
                            JOIN asha_workers aw
                                ON aw.supervisor_id = s.supervisor_id
                            WHERE aw.asha_id = :asha_id
                            AND s.is_active = TRUE
                        """),
                        {"asha_id": alert["asha_id"]}
                    ).fetchone()
                else:
                    result = conn.execute(
                        text("""
                            SELECT phone, name FROM asha_supervisors
                            WHERE supervisor_id = :id
                            AND is_active = TRUE
                        """),
                        {"id": supervisor_id}
                    ).fetchone()

                if result:
                    return result.phone, result.name
                return None, None

            elif target_level == 2:
                # Escalate to BMO
                bmo_id = alert.get("bmo_id", "")
                if not bmo_id:
                    # Find BMO via supervisor chain
                    result = conn.execute(
                        text("""
                            SELECT b.phone, b.name
                            FROM block_officers b
                            JOIN asha_supervisors s
                                ON s.bmo_id = b.bmo_id
                            JOIN asha_workers aw
                                ON aw.supervisor_id = s.supervisor_id
                            WHERE aw.asha_id = :asha_id
                            AND b.is_active = TRUE
                        """),
                        {"asha_id": alert["asha_id"]}
                    ).fetchone()
                else:
                    result = conn.execute(
                        text("""
                            SELECT phone, name FROM block_officers
                            WHERE bmo_id = :id AND is_active = TRUE
                        """),
                        {"id": bmo_id}
                    ).fetchone()

                if result:
                    return result.phone, result.name
                return None, None

            elif target_level == 3:
                # Escalate to DHO — use env variable
                dho_phone = DHO_PHONE
                if dho_phone:
                    return dho_phone, "District Health Officer"
                # Fallback — get first admin phone
                result = conn.execute(
                    text("SELECT phone, name FROM admins WHERE phone IS NOT NULL LIMIT 1")
                ).fetchone()
                if result:
                    return result.phone, result.name
                return None, None

    except Exception as e:
        print(f"Get escalation phone error: {e}")
        return None, None


# ─────────────────────────────────────────────────────────────────
# ALSO NOTIFY ASHA WORKER — reminder at each escalation
# ─────────────────────────────────────────────────────────────────

def send_asha_reminder(alert):
    """
    Sends a reminder to the ASHA worker when her alert is escalated.
    She should know her supervisor has been informed.
    """
    from database import engine

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT phone, name FROM asha_workers WHERE asha_id = :id"),
                {"id": alert["asha_id"]}
            ).fetchone()

            if result:
                message = (
                    f"⚠️ Reminder — MaaSakhi\n\n"
                    f"You have a PENDING high-risk alert that has not been attended:\n\n"
                    f"Patient: {alert['name']}\n"
                    f"Week: {alert['week']}\n"
                    f"Symptom: {alert['symptom']}\n"
                    f"Address: {alert.get('address', 'Not provided')}\n\n"
                    f"Your supervisor has been informed.\n"
                    f"Please attend this patient immediately or confirm status."
                )
                send_whatsapp(result.phone, message)

    except Exception as e:
        print(f"ASHA reminder error: {e}")


# ─────────────────────────────────────────────────────────────────
# CORE ESCALATION CHECK — runs on a schedule
# ─────────────────────────────────────────────────────────────────

def run_escalation_check():
    """
    Checks all pending alerts and escalates if no response.
    Should be called every 30 minutes via background thread.
    """
    from database import engine, escalate_alert, log_escalation

    if not engine:
        return

    print(f"[Escalation check] Running at {datetime.now().strftime('%H:%M:%S')}")

    try:
        with engine.connect() as conn:

            # Get ALL pending or attended alerts that may need escalation
            results = conn.execute(text("""
                SELECT
                    aa.*,
                    aw.name  as asha_name,
                    aw.phone as asha_phone,
                    aw.supervisor_id
                FROM asha_alerts aa
                JOIN asha_workers aw ON aa.asha_id = aw.asha_id
                WHERE aa.status IN ('Pending', 'Attended')
                AND aa.escalation_level < 3
                ORDER BY aa.created_at ASC
            """)).fetchall()

        for r in results:
            alert = {
                "id":            r.id,
                "phone":         r.phone,
                "name":          r.name,
                "week":          r.week,
                "symptom":       r.symptom,
                "address":       r.address     if r.address     else "",
                "village":       r.village     if r.village     else "",
                "maps_link":     r.maps_link   if r.maps_link   else "",
                "asha_id":       r.asha_id,
                "asha_name":     r.asha_name,
                "asha_phone":    r.asha_phone,
                "supervisor_id": r.supervisor_id if r.supervisor_id else "",
                "bmo_id":        r.bmo_id         if r.bmo_id         else "",
                "status":        r.status,
                "level":         r.escalation_level,
                "created_at":    r.created_at
            }

            now          = datetime.now()
            current_level = alert["level"]
            hours_needed  = ESCALATION_HOURS.get(current_level)

            if not hours_needed:
                continue

            # Check if enough time has passed for this escalation level
            time_threshold = alert["created_at"] + timedelta(hours=hours_needed)

            # Also check escalated_at if already escalated once
            if r.escalated_at:
                next_threshold = r.escalated_at + timedelta(hours=2)
                time_threshold = max(time_threshold, next_threshold)

            if now < time_threshold:
                continue  # Not time yet

            # ── Escalate! ──────────────────────────────────────
            target_level = current_level + 1
            to_phone, to_name = get_escalation_phone(alert, target_level, engine)

            if not to_phone:
                print(f"[Escalation] No phone found for level {target_level} — alert {alert['id']}")
                # Still bump the level so we don't keep retrying same level
                escalate_alert(alert["id"], target_level)
                continue

            # Build and send escalation message
            message = build_escalation_message(alert, target_level, to_name)
            sent    = send_whatsapp(to_phone, message)

            if sent:
                # Update alert escalation level
                escalate_alert(alert["id"], target_level)

                # Log to audit trail
                role_names = {1: "supervisor", 2: "bmo", 3: "dho"}
                log_escalation(
                    alert_id  = alert["id"],
                    from_role = "asha",
                    to_role   = role_names.get(target_level, "dho"),
                    to_phone  = to_phone,
                    reason    = (
                        f"No response after {hours_needed} hours. "
                        f"Escalated to {to_name} ({to_phone})"
                    )
                )

                # Send reminder to original ASHA worker
                send_asha_reminder(alert)

                print(
                    f"[Escalation] Alert {alert['id']} escalated to "
                    f"level {target_level} — sent to {to_name} ({to_phone})"
                )

    except Exception as e:
        print(f"[Escalation check error]: {e}")


# ─────────────────────────────────────────────────────────────────
# BACKGROUND THREAD — runs every 30 minutes automatically
# ─────────────────────────────────────────────────────────────────

def start_escalation_engine():
    """
    Starts the escalation engine as a background thread.
    Call this once from app.py on startup.
    Runs forever — checks every 30 minutes.
    """
    def engine_loop():
        # Wait 60 seconds after startup before first check
        # (lets the database finish initializing)
        time.sleep(60)

        while True:
            try:
                run_escalation_check()
            except Exception as e:
                print(f"[Escalation engine error]: {e}")

            # Wait 30 minutes before next check
            time.sleep(30 * 60)

    thread = threading.Thread(
        target=engine_loop,
        daemon=True,      # Dies when main app dies — no orphan threads
        name="EscalationEngine"
    )
    thread.start()
    print("✅ Escalation engine started — checking every 30 minutes")


# ─────────────────────────────────────────────────────────────────
# MANUAL TRIGGER — for testing or admin use
# ─────────────────────────────────────────────────────────────────

def trigger_manual_escalation(alert_id):
    """
    Manually escalates a specific alert immediately.
    Used by supervisor/admin from dashboard.
    """
    from database import get_alert_by_id, engine

    alert = get_alert_by_id(alert_id)
    if not alert:
        return False, "Alert not found"

    current_level = alert["level"]
    if current_level >= 3:
        return False, "Already escalated to highest level (DHO)"

    target_level          = current_level + 1
    to_phone, to_name     = get_escalation_phone(alert, target_level, engine)

    if not to_phone:
        return False, f"No contact found for level {target_level}"

    message = build_escalation_message(alert, target_level, to_name)
    sent    = send_whatsapp(to_phone, message)

    if sent:
        from database import escalate_alert, log_escalation
        escalate_alert(alert_id, target_level)

        role_names = {1: "supervisor", 2: "bmo", 3: "dho"}
        log_escalation(
            alert_id  = alert_id,
            from_role = "manual",
            to_role   = role_names.get(target_level, "dho"),
            to_phone  = to_phone,
            reason    = f"Manually escalated to {to_name}"
        )
        return True, f"Escalated to {to_name} ({to_phone})"

    return False, "Failed to send WhatsApp message"