# ─────────────────────────────────────────────────────────────────
# MaaSakhi Escalation Engine
# Auto-escalates unresponded alerts up the 5-tier hierarchy
#
# Timeline (relative to LAST action, not alert creation):
#   T+0h  → Alert created → sent to ASHA worker (level 0)
#   T+2h  → ASHA no response → Supervisor (level 1)
#   T+2h  → Supervisor no response → BMO (level 2)
#   T+2h  → BMO no response → DHO / Admin (level 3)
#
# Each tier gets exactly 2 hours before the next escalation.
# The clock resets at each escalation (uses escalated_at, not created_at).
# ─────────────────────────────────────────────────────────────────

import os
import threading
import time
from datetime import datetime, timedelta
from twilio.rest import Client
from sqlalchemy import text

TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID",     "")
TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN",       "")
TWILIO_WHATSAPP_FROM   = "whatsapp:+14155238886"
TWILIO_SMS_FROM        = os.environ.get("TWILIO_SMS_FROM",         "")   # SMS fallback
DHO_PHONE              = os.environ.get("DHO_PHONE",               "")

# Hours of silence before escalating from each level
ESCALATION_WINDOW_HRS = 2   # every level gets 2 hrs

# Background thread interval
CHECK_INTERVAL_SECS   = 15 * 60   # every 15 minutes


# ─────────────────────────────────────────────────────────────────
# WHATSAPP + SMS HELPERS
# ─────────────────────────────────────────────────────────────────

def _twilio_client():
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_whatsapp(to_phone: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    Normalises the phone number (adds whatsapp: prefix if missing).
    Returns True on success.
    """
    if not to_phone:
        print("[escalation] send_whatsapp: no phone number — skipped")
        return False
    if not to_phone.startswith("whatsapp:"):
        to_phone = "whatsapp:" + to_phone
    try:
        msg = _twilio_client().messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=to_phone,
            body=message
        )
        print(f"[escalation] WhatsApp sent → {to_phone} | SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"[escalation] WhatsApp error → {to_phone}: {e}")
        return False


def _send_sms_fallback(to_phone: str, message: str) -> bool:
    """
    SMS fallback — only used when WhatsApp delivery fails AND
    TWILIO_SMS_FROM env var is set.
    Strips any whatsapp: prefix before sending.
    """
    if not TWILIO_SMS_FROM or not to_phone:
        return False
    clean = to_phone.replace("whatsapp:", "").strip()
    try:
        msg = _twilio_client().messages.create(
            from_=TWILIO_SMS_FROM,
            to=clean,
            body=message[:1600]          # SMS limit safety
        )
        print(f"[escalation] SMS fallback sent → {clean} | SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"[escalation] SMS fallback error → {clean}: {e}")
        return False


def _send_with_fallback(to_phone: str, message: str) -> bool:
    """Try WhatsApp first; fall back to SMS if it fails."""
    if send_whatsapp(to_phone, message):
        return True
    print(f"[escalation] WhatsApp failed → trying SMS fallback for {to_phone}")
    return _send_sms_fallback(to_phone, message)


# ─────────────────────────────────────────────────────────────────
# ESCALATION MESSAGE BUILDER
# ─────────────────────────────────────────────────────────────────

def build_escalation_message(alert: dict, target_level: int,
                              recipient_name: str) -> str:
    """
    Builds the WhatsApp/SMS message for a given escalation level.
    target_level: 1 = Supervisor, 2 = BMO, 3 = DHO
    """
    maps_line = (
        f"\n📌 Navigate to patient:\n{alert['maps_link']}"
        if alert.get("maps_link") else ""
    )

    created_str = (
        alert["created_at"].strftime("%d %b %Y, %I:%M %p")
        if hasattr(alert.get("created_at"), "strftime")
        else str(alert.get("created_at", ""))
    )

    headers = {
        1: "⚠️ ESCALATION — ASHA Worker Not Responded",
        2: "🔴 URGENT — Supervisor Not Responded",
        3: "🚨 CRITICAL — BMO Not Responded",
    }

    context = {
        1: (
            f"ASHA worker *{alert.get('asha_name','—')}* was alerted "
            "2 hours ago but has NOT attended the patient.\n"
            "Please contact the ASHA or visit the patient directly."
        ),
        2: (
            "This alert was escalated to the Supervisor 2 hours ago "
            "but remains unresolved.\n"
            "Immediate block-level intervention is required."
        ),
        3: (
            "This alert has been escalating for 6+ hours with no resolution.\n"
            "CRITICAL: District-level intervention is required immediately."
        ),
    }

    return (
        f"{headers.get(target_level, '🚨 ESCALATION')}\n\n"
        f"👤 Patient:  {alert['name']}\n"
        f"🤰 Week:     {alert['week']}\n"
        f"⚠️ Symptom: {alert['symptom']}\n"
        f"📞 Phone:   {alert['phone']}\n"
        f"📍 Village: {alert.get('village', '—')}\n"
        f"🏠 Address: {alert.get('address', '—')}\n"
        f"🕐 Alert raised: {created_str}"
        f"{maps_line}\n\n"
        f"{context.get(target_level, '')}\n\n"
        f"— MaaSakhi Escalation System"
    )


def _build_asha_reminder(alert: dict) -> str:
    return (
        f"⚠️ *Reminder — MaaSakhi*\n\n"
        f"You have a PENDING high-risk alert that is still unattended:\n\n"
        f"👤 Patient: {alert['name']}\n"
        f"🤰 Week: {alert['week']}\n"
        f"⚠️ Symptom: {alert['symptom']}\n"
        f"🏠 Address: {alert.get('address', '—')}\n\n"
        f"Your supervisor has been informed.\n"
        f"Please attend this patient immediately or update status.\n\n"
        f"— MaaSakhi"
    )


# ─────────────────────────────────────────────────────────────────
# PHONE LOOKUP — find the correct contact for each level
# ─────────────────────────────────────────────────────────────────

def get_escalation_target(alert: dict, target_level: int,
                           engine) -> tuple[str | None, str]:
    """
    Returns (phone, name) for the recipient at `target_level`.
    target_level: 1 = Supervisor, 2 = BMO, 3 = DHO

    Lookup order:
      - Use stored ID on the alert first (fastest)
      - Walk up the hierarchy if ID is missing
      - Fall back to DHO_PHONE env var at level 3
    """
    if not engine:
        return None, "Unknown"

    try:
        with engine.connect() as conn:

            # ── Level 1: Supervisor ───────────────────────────────
            if target_level == 1:
                sup_id = alert.get("supervisor_id", "")
                if sup_id:
                    row = conn.execute(text("""
                        SELECT phone, name FROM asha_supervisors
                        WHERE supervisor_id = :id AND is_active = TRUE
                    """), {"id": sup_id}).fetchone()
                else:
                    row = conn.execute(text("""
                        SELECT s.phone, s.name
                        FROM asha_supervisors s
                        JOIN asha_workers aw ON aw.supervisor_id = s.supervisor_id
                        WHERE aw.asha_id = :asha_id AND s.is_active = TRUE
                        LIMIT 1
                    """), {"asha_id": alert["asha_id"]}).fetchone()

                if row:
                    return row.phone, row.name
                return None, "Supervisor"

            # ── Level 2: BMO ──────────────────────────────────────
            elif target_level == 2:
                bmo_id = alert.get("bmo_id", "")
                if bmo_id:
                    row = conn.execute(text("""
                        SELECT phone, name FROM block_officers
                        WHERE bmo_id = :id AND is_active = TRUE
                    """), {"id": bmo_id}).fetchone()
                else:
                    row = conn.execute(text("""
                        SELECT b.phone, b.name
                        FROM block_officers b
                        JOIN asha_supervisors s ON s.bmo_id = b.bmo_id
                        JOIN asha_workers aw ON aw.supervisor_id = s.supervisor_id
                        WHERE aw.asha_id = :asha_id AND b.is_active = TRUE
                        LIMIT 1
                    """), {"asha_id": alert["asha_id"]}).fetchone()

                if row:
                    return row.phone, row.name
                return None, "BMO"

            # ── Level 3: DHO ──────────────────────────────────────
            elif target_level == 3:
                # Prefer env var (set by admin in Railway)
                if DHO_PHONE:
                    return DHO_PHONE, "District Health Officer"
                # Fallback: first admin with a phone number
                row = conn.execute(text("""
                    SELECT phone, name FROM admins
                    WHERE phone IS NOT NULL LIMIT 1
                """)).fetchone()
                if row:
                    return row.phone, row.name
                return None, "DHO"

    except Exception as e:
        print(f"[escalation] get_escalation_target error (level {target_level}): {e}")

    return None, "Unknown"


def _get_asha_phone(asha_id: str, engine) -> str | None:
    """Look up the WhatsApp/phone number for an ASHA worker."""
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT phone FROM asha_workers WHERE asha_id = :id"),
                {"id": asha_id}
            ).fetchone()
            return row.phone if row else None
    except Exception as e:
        print(f"[escalation] _get_asha_phone error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# CORE: decide if an alert should be escalated right now
# ─────────────────────────────────────────────────────────────────

def _should_escalate(alert_row) -> bool:
    """
    Returns True if this alert has been sitting at its current
    escalation level for >= ESCALATION_WINDOW_HRS without resolution.

    Clock logic:
      - If never escalated before → use created_at as the reference
      - If already escalated → use escalated_at as the reference
        (so each tier gets exactly 2 hrs, not cumulative)
    """
    now           = datetime.now()
    current_level = alert_row.escalation_level

    if current_level >= 3:
        return False    # already at highest level

    # Reference time: when did the *current* level start?
    if alert_row.escalated_at and current_level > 0:
        reference = alert_row.escalated_at
    else:
        reference = alert_row.created_at

    threshold = reference + timedelta(hours=ESCALATION_WINDOW_HRS)
    return now >= threshold


# ─────────────────────────────────────────────────────────────────
# MAIN CHECK — called by background thread or /cron/escalate
# ─────────────────────────────────────────────────────────────────

def run_escalation_check() -> int:
    """
    Scans all un-resolved alerts and escalates any that have exceeded
    the 2-hour window at their current level.

    Returns the number of alerts actually escalated this run.
    (app.py uses this return value for the /cron/escalate response.)
    """
    from database import engine, escalate_alert, log_escalation

    if not engine:
        print("[escalation] No DB engine — skipping check")
        return 0

    escalated_count = 0
    print(f"[escalation] Check started — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    aa.*,
                    aw.name          AS asha_name,
                    aw.phone         AS asha_phone,
                    aw.supervisor_id AS asha_supervisor_id
                FROM asha_alerts aa
                JOIN asha_workers aw ON aa.asha_id = aw.asha_id
                WHERE aa.status IN ('Pending', 'Attended')
                  AND aa.escalation_level < 3
                ORDER BY aa.created_at ASC
            """)).fetchall()

    except Exception as e:
        print(f"[escalation] DB query error: {e}")
        return 0

    for r in rows:
        if not _should_escalate(r):
            continue

        current_level = r.escalation_level
        target_level  = current_level + 1

        alert = {
            "id":            r.id,
            "phone":         r.phone,
            "name":          r.name,
            "week":          r.week,
            "symptom":       r.symptom,
            "address":       r.address      or "",
            "village":       r.village      or "",
            "maps_link":     r.maps_link    or "",
            "asha_id":       r.asha_id,
            "asha_name":     r.asha_name    or "—",
            "asha_phone":    r.asha_phone   or "",
            "supervisor_id": r.supervisor_id or r.asha_supervisor_id or "",
            "bmo_id":        r.bmo_id        or "",
            "status":        r.status,
            "level":         current_level,
            "created_at":    r.created_at
        }

        to_phone, to_name = get_escalation_target(alert, target_level, engine)

        if not to_phone:
            print(
                f"[escalation] Alert {alert['id']}: no contact at level "
                f"{target_level} — bumping level without sending"
            )
            # Bump anyway so we don't retry the same broken level forever
            escalate_alert(alert["id"], target_level)
            log_escalation(
                alert_id  = alert["id"],
                from_role = _level_role(current_level),
                to_role   = _level_role(target_level),
                to_phone  = "NOT_FOUND",
                reason    = f"No contact found for level {target_level} — level bumped"
            )
            escalated_count += 1
            continue

        message = build_escalation_message(alert, target_level, to_name)
        sent    = _send_with_fallback(to_phone, message)

        if sent:
            escalate_alert(alert["id"], target_level)
            log_escalation(
                alert_id  = alert["id"],
                from_role = _level_role(current_level),
                to_role   = _level_role(target_level),
                to_phone  = to_phone,
                reason    = (
                    f"Auto-escalated: no response at level {current_level} "
                    f"after {ESCALATION_WINDOW_HRS}h → {to_name}"
                )
            )
            # Remind the original ASHA worker
            if alert["asha_phone"]:
                _send_with_fallback(
                    alert["asha_phone"],
                    _build_asha_reminder(alert)
                )
            escalated_count += 1
            print(
                f"[escalation] Alert {alert['id']} → level {target_level} "
                f"({to_name} · {to_phone})"
            )
        else:
            print(
                f"[escalation] Alert {alert['id']}: all delivery attempts "
                f"failed for level {target_level} ({to_phone})"
            )

    print(
        f"[escalation] Check complete — "
        f"{escalated_count} escalated / {len(rows)} checked"
    )
    return escalated_count


def _level_role(level: int) -> str:
    return {0: "asha", 1: "supervisor", 2: "bmo", 3: "dho"}.get(level, "unknown")


# ─────────────────────────────────────────────────────────────────
# BACKGROUND THREAD
# ─────────────────────────────────────────────────────────────────

def start_escalation_engine():
    """
    Starts the escalation engine as a daemon background thread.
    Call once from app.py on startup.
    Waits 60 s after startup, then runs every 15 minutes.
    """
    def _loop():
        time.sleep(60)    # let DB initialise fully
        while True:
            try:
                run_escalation_check()
            except Exception as e:
                print(f"[escalation engine] Unhandled error: {e}")
            time.sleep(CHECK_INTERVAL_SECS)

    t = threading.Thread(target=_loop, daemon=True, name="EscalationEngine")
    t.start()
    print(
        f"✅ Escalation engine started — "
        f"checking every {CHECK_INTERVAL_SECS // 60} minutes"
    )


# ─────────────────────────────────────────────────────────────────
# MANUAL TRIGGER — from supervisor/BMO dashboard buttons
# ─────────────────────────────────────────────────────────────────

def trigger_manual_escalation(alert_id: int,
                               reason: str = "") -> tuple[bool, str]:
    """
    Immediately escalates a specific alert to the next level.
    Called from:
      - /supervisor/<id>/escalate/<alert_id>
      - /bmo/<id>/escalate/<alert_id>

    Returns (success: bool, message: str).
    """
    from database import get_alert_by_id, engine, escalate_alert, log_escalation

    alert = get_alert_by_id(alert_id)
    if not alert:
        return False, "Alert not found"

    current_level = alert.get("level", 0)
    if current_level >= 3:
        return False, "Already at highest escalation level (DHO)"

    target_level          = current_level + 1
    to_phone, to_name     = get_escalation_target(alert, target_level, engine)

    if not to_phone:
        return False, f"No contact found for level {target_level}"

    # Enrich alert with asha_name if missing
    if not alert.get("asha_name"):
        try:
            from sqlalchemy import text as sqlt
            with engine.connect() as conn:
                row = conn.execute(
                    sqlt("SELECT name FROM asha_workers WHERE asha_id = :id"),
                    {"id": alert["asha_id"]}
                ).fetchone()
                alert["asha_name"] = row.name if row else "—"
        except Exception:
            alert["asha_name"] = "—"

    message = build_escalation_message(alert, target_level, to_name)
    sent    = _send_with_fallback(to_phone, message)

    if sent:
        escalate_alert(alert_id, target_level)
        log_escalation(
            alert_id  = alert_id,
            from_role = _level_role(current_level),
            to_role   = _level_role(target_level),
            to_phone  = to_phone,
            reason    = reason or f"Manually escalated to {to_name}"
        )
        # Remind ASHA worker
        asha_phone = _get_asha_phone(alert["asha_id"], engine)
        if asha_phone:
            _send_with_fallback(asha_phone, _build_asha_reminder(alert))

        return True, f"Escalated to {to_name} ({to_phone})"

    return False, f"Message delivery failed for {to_phone}"