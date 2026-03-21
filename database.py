# ─────────────────────────────────────────────────────────────────
# MaaSakhi Database Layer
# PostgreSQL via SQLAlchemy
# Stores: patients, symptoms, alerts permanently
# ─────────────────────────────────────────────────────────────────

import os
from datetime import datetime
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Fix Railway PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL) if DATABASE_URL else None


def init_db():
    """Create all tables if they don't exist."""
    if not engine:
        print("No database URL found — using memory mode")
        return

    with engine.connect() as conn:
        # Patients table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS patients (
                phone       TEXT PRIMARY KEY,
                name        TEXT,
                week        INTEGER,
                step        TEXT DEFAULT 'welcome',
                language    TEXT DEFAULT 'Hindi',
                created_at  TIMESTAMP DEFAULT NOW(),
                updated_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # Symptom logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS symptom_logs (
                id          SERIAL PRIMARY KEY,
                phone       TEXT,
                week        INTEGER,
                message     TEXT,
                level       TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # ASHA alerts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asha_alerts (
                id          SERIAL PRIMARY KEY,
                phone       TEXT,
                name        TEXT,
                week        INTEGER,
                symptom     TEXT,
                status      TEXT DEFAULT 'Pending',
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        conn.commit()
        print("Database tables created successfully!")


# ── Patient functions ─────────────────────────────────────────────

def get_patient(phone):
    """Get patient from database. Returns dict or None."""
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM patients WHERE phone = :phone"),
                {"phone": phone}
            ).fetchone()
            if result:
                return {
                    "phone":    result.phone,
                    "name":     result.name,
                    "week":     result.week,
                    "step":     result.step,
                    "language": result.language
                }
            return None
    except Exception as e:
        print(f"Database get_patient error: {e}")
        return None


def save_patient(phone, name, week, step, language="Hindi"):
    """Save or update patient in database."""
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO patients (phone, name, week, step, language, updated_at)
                VALUES (:phone, :name, :week, :step, :language, NOW())
                ON CONFLICT (phone) DO UPDATE SET
                    name       = :name,
                    week       = :week,
                    step       = :step,
                    language   = :language,
                    updated_at = NOW()
            """), {
                "phone":    phone,
                "name":     name,
                "week":     week,
                "step":     step,
                "language": language
            })
            conn.commit()
    except Exception as e:
        print(f"Database save_patient error: {e}")


def get_all_patients():
    """Get all registered patients."""
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("SELECT * FROM patients WHERE step = 'registered'")
            ).fetchall()
            patients = {}
            for r in results:
                patients[r.phone] = {
                    "phone":    r.phone,
                    "name":     r.name,
                    "week":     r.week,
                    "step":     r.step,
                    "language": r.language
                }
            return patients
    except Exception as e:
        print(f"Database get_all_patients error: {e}")
        return {}


# ── Symptom log functions ─────────────────────────────────────────

def save_symptom_log(phone, week, message, level):
    """Save symptom to database."""
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO symptom_logs (phone, week, message, level)
                VALUES (:phone, :week, :message, :level)
            """), {
                "phone":   phone,
                "week":    week,
                "message": message,
                "level":   level
            })
            conn.commit()
    except Exception as e:
        print(f"Database save_symptom_log error: {e}")


def get_symptom_logs(phone):
    """Get all symptom logs for a patient."""
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM symptom_logs
                    WHERE phone = :phone
                    ORDER BY created_at ASC
                """),
                {"phone": phone}
            ).fetchall()
            return [{
                "week":    r.week,
                "message": r.message,
                "level":   r.level,
                "time":    r.created_at.strftime("%d %b %Y, %I:%M %p")
            } for r in results]
    except Exception as e:
        print(f"Database get_symptom_logs error: {e}")
        return []


def get_risk_score_from_db(phone):
    """Calculate risk score from database logs."""
    logs = get_symptom_logs(phone)

    if not logs:
        return 0, "Unknown", "No reports yet"

    red_count   = sum(1 for e in logs if e["level"] == "RED")
    amber_count = sum(1 for e in logs if e["level"] == "AMBER")
    green_count = sum(1 for e in logs if e["level"] == "GREEN")
    total       = len(logs)

    score = min(100, (red_count * 40) + (amber_count * 15) + (green_count * 2))

    recent      = logs[-3:] if len(logs) >= 3 else logs
    recent_reds = sum(1 for e in recent if e["level"] == "RED")
    if recent_reds >= 2:
        score = min(100, score + 20)

    if score >= 60 or red_count >= 2:
        risk_level = "HIGH"
    elif score >= 30 or red_count >= 1:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    summary = (
        f"Total: {total} | "
        f"Danger: {red_count} | "
        f"Warning: {amber_count} | "
        f"Normal: {green_count}"
    )

    return score, risk_level, summary


# ── ASHA alert functions ──────────────────────────────────────────

def save_asha_alert_db(phone, name, week, symptom):
    """Save ASHA alert to database."""
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO asha_alerts (phone, name, week, symptom)
                VALUES (:phone, :name, :week, :symptom)
            """), {
                "phone":   phone,
                "name":    name,
                "week":    week,
                "symptom": symptom
            })
            conn.commit()
    except Exception as e:
        print(f"Database save_asha_alert error: {e}")


def get_all_asha_alerts():
    """Get all ASHA alerts from database."""
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM asha_alerts
                    ORDER BY created_at DESC
                """)
            ).fetchall()
            return [{
                "name":    r.name,
                "week":    r.week,
                "symptom": r.symptom,
                "phone":   r.phone,
                "time":    r.created_at.strftime("%d %b %Y, %I:%M %p"),
                "status":  r.status
            } for r in results]
    except Exception as e:
        print(f"Database get_all_asha_alerts error: {e}")
        return []


def get_alert_count_db():
    """Get total alert count from database."""
    if not engine:
        return 0
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM asha_alerts")
            ).fetchone()
            return result[0]
    except Exception as e:
        print(f"Database get_alert_count error: {e}")
        return 0